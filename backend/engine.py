import asyncio
import httpx
import datetime
import json
import re
import traceback
import uuid
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    Department, Agent, Thread, LogAction, LogLedger,
    PromptTemplate, Setting, AgentTool, SystemLog,
    ThreadCollaborator, JoinQuest, Message, Ticket
)


class SimEngine:
    def __init__(self):
        self.counter = 0
        self.running = False
        self.subscribers: list = []   # active WebSocket connections

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self):
        self.running = True
        while self.running:
            await self.tick()
            await asyncio.sleep(1)

    def stop(self):
        self.running = False

    # ── WebSocket broadcast ───────────────────────────────────────────────────

    async def broadcast(self, message: dict):
        dead = []
        for ws in list(self.subscribers):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.subscribers:
                self.subscribers.remove(ws)

    # ── Logging helper ────────────────────────────────────────────────────────

    async def log(self, db, level: str, category: str, event: str,
                  details: dict = None, agent_id: str = None, dept_id: str = None):
        """Write a structured log entry to DB and broadcast it live."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry = SystemLog(
            time=now, level=level, category=category,
            event=event, agent_id=agent_id, dept_id=dept_id,
            details=json.dumps(details or {})
        )
        try:
            db.add(entry)
        except Exception:
            pass   # never let logging crash the engine
        log_data = {
            "time": now, "level": level, "category": category,
            "event": event, "details": details or {},
            "agent_id": agent_id, "dept_id": dept_id
        }
        await self.broadcast({"type": "log", "log": log_data})
        return log_data

    # ── Main tick loop ────────────────────────────────────────────────────────

    async def tick(self):
        self.counter += 1
        if self.counter >= 3600:
            self.counter = 0

        db: Session = SessionLocal()
        try:
            agents = db.query(Agent).all()
            ticking_agents = [a for a in agents if a.ticks > 0 and self.counter % a.ticks == 0]
            print(ticking_agents)
            # Broadcast heartbeat every second (lightweight – no DB write)
            await self.broadcast({"type": "heartbeat", "counter": self.counter})

            # DB log every 10 s so the Logger has periodic engine checkpoints
            if self.counter % 10 == 0:
                await self.log(db, "TICK", "ENGINE", "HEARTBEAT", {
                    "counter": self.counter,
                    "total_agents": len(agents),
                    "ticking_now": len(ticking_agents),
                })
                db.commit()

            if not ticking_agents:
                return

            # ── Gather tool context once per tick ───────────────────────────
            enabled_tools = db.query(AgentTool).filter(AgentTool.enabled == True).all()
            s_prefix = db.query(Setting).filter(Setting.key == "tools_instruction_prefix").first()
            prefix = s_prefix.value if s_prefix else "AVAILABLE TOOLS:\n"
            tools_block = (
                prefix + "\n" + "\n".join([f"- {t.description}" for t in enabled_tools])
                if enabled_tools else "No tools currently available."
            )

            # ── Thread Maintenance (Taxation) ───────────────────────────────
            await self.process_thread_maintenance(db)
            await self.handle_quest_expirations(db)

            task_coros = []

            for agent in ticking_agents:
                dept = agent.department

                # ── Apply pending mode change ────────────────────────────────
                if agent.next_mode:
                    old_mode = agent.mode
                    agent.mode = agent.next_mode
                    agent.next_mode = None
                    await self.log(db, "INFO", "AGENT", "MODE_CHANGE",
                                   {"from": old_mode, "to": agent.mode},
                                   agent_id=agent.id, dept_id=dept.id if dept else None)

                # ── Tool descriptions with context ───────────────────────────
                active_threads = db.query(Thread).filter(Thread.status == "ACTIVE").all()
                t_context = "\n".join([f"ID: {t.id} | Topic: {t.topic} | Budget: {t.budget}pt" for t in active_threads]) if active_threads else "No active public threads."
                agent_tools_prompt = f"{tools_block}\n\nACTIVE THREADS:\n{t_context}"

                # ── Point deduction & Execution ──────────────────────────────
                can_tick = await self.deduct_points(db, agent, 1, "tick")
                if can_tick:
                    task_coros.append(self.handle_agent_tick(agent.id, agent_tools_prompt))
                else:
                    await self.log(db, "WARN", "AGENT", "TICK_SKIPPED_NO_POINTS", {
                        "agent": agent.name_id,
                        "wallet": agent.wallet_current,
                        "dept_balance": dept.ledger_current if dept else 0
                    }, agent_id=agent.id, dept_id=dept.id if dept else None)

            if task_coros:
                await asyncio.gather(*task_coros)

            db.commit()
        except Exception:
            print("Engine Tick Exception:")
            traceback.print_exc()
        finally:
            db.close()

    async def handle_agent_tick(self, agent_id, tools_block):
        db: Session = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent: return
            
            # 1. Get Prompts
            # 2. Context
            inv_context = self.get_rich_invitation_context(db, agent)
            tkt_context = self.get_available_tickets_context(db)
            # Find last quest for status placeholder
            last_q = db.query(JoinQuest).filter(JoinQuest.agent_id == agent.id).order_by(JoinQuest.id.desc()).first()
            q_status = last_q.status if last_q else "None"

            # Last actions
            actions = db.query(LogAction).filter(LogAction.agent_id == agent.id).order_by(LogAction.id.desc()).limit(5).all()
            actions_str = "\n".join([f"- {a.what} ({a.points} pts)" for a in actions]) if actions else "No recent actions."
            
            dept_info = f"Department: {agent.department.name} (Balance: {agent.department.ledger_current} pts)" if agent.department else "No Department"
            
            system_prompt = p_template.system_prompt
            
            # Injection logic for placeholders
            directives = (p_template.custom_directives or "").replace("{{pending_invitation}}", inv_context).replace("{{invitation_status}}", q_status).replace("{{available_tickets}}", tkt_context)

            user_prompt = p_template.user_prompt_template.format(
                name=agent.name_id,
                id=agent.id,
                wallet=agent.wallet_current,
                dept=dept_info,
                memory=agent.memory or "None",
                actions=actions_str,
                tools=tools_block,
                directives=directives,
                message=""
            )
            # Second pass for placeholders in the formatted template
            # If the template used {{pending_invitation}}, it became {pending_invitation} after .format()
            user_prompt = user_prompt.replace("{{pending_invitation}}", inv_context).replace("{pending_invitation}", inv_context)
            user_prompt = user_prompt.replace("{{invitation_status}}", q_status).replace("{invitation_status}", q_status)
            user_prompt = user_prompt.replace("{{available_tickets}}", tkt_context).replace("{available_tickets}", tkt_context)

            # 3. Call LLM
            s_url = db.query(Setting).filter(Setting.key == "ollama_server").first()
            s_mod = db.query(Setting).filter(Setting.key == "ollama_model").first()
            server = s_url.value if s_url else "http://localhost:11434"
            model  = s_mod.value if s_mod else "gemma4:e4b"

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{server}/api/generate",
                    json={
                        "model": model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "stream": False
                    },
                    timeout=90.0
                )
                raw = resp.json().get("response", "")

            # 4. Handle State [MEMORY]...[END MEMORY] and [MODE]...[END MODE]
            mem_match = re.search(r"\[MEMORY\](.*?)\s*\[END MEMORY\]", raw, re.DOTALL | re.IGNORECASE)
            if mem_match:
                agent.memory = mem_match.group(1).strip()[:200]
                raw = raw.replace(mem_match.group(0), "").strip()

            mode_match = re.search(r"\[MODE\](.*?)\s*\[END MODE\]", raw, re.DOTALL | re.IGNORECASE)
            if mode_match:
                next_val = mode_match.group(1).strip()
                # Validation with Fallback: only set if mode exists
                exists = db.query(PromptTemplate).filter(PromptTemplate.id == next_val).first()
                if exists:
                    agent.next_mode = next_val
                raw = raw.replace(mode_match.group(0), "").strip()

            # 5. Handle Tools
            processed_raw, tool_results = await self.handle_tools(db, agent, raw)
            
            # 6. Final Logic: Log Action
            action_snippet = processed_raw[:250] + ("..." if len(processed_raw) > 250 else "")
            db.add(LogAction(agent_id=agent.id, what=action_snippet, points=0))
            
            # Prepare rich details for System Logger
            prompt_preview = f"SYSTEM:\n{system_prompt[:200]}...\n\nUSER:\n{user_prompt[:200]}..."
            response_preview = processed_raw

            await self.log(db, "INFO", "AGENT", "TICK_COMPLETE", {
                "agent": agent.name_id,
                "prompt_preview": prompt_preview,
                "response_preview": response_preview,
                "action": action_snippet,
                "tool_results": tool_results
            }, agent_id=agent.id, dept_id=agent.department_id)

            # 7. Broadcast to Activity Feed
            await self.broadcast({
                "type": "feed",
                "feed_item": {
                    "agent": agent.name_id,
                    "dept": agent.department_id,
                    "msg": action_snippet,
                    "full_msg": response_preview
                }
            })
            
            db.commit()

        except Exception as e:
            await self.log(db, "ERROR", "ENGINE", "LLM_ERROR", {
                "agent": agent_id, "error": str(e)
            }, agent_id=agent_id)
            print(f"Agent {agent_id} LLM error: {e}")
            traceback.print_exc()
        finally:
            db.close()

    # ── Thread Maintenance ───────────────────────────────────────────────────

    async def process_thread_maintenance(self, db):
        """Handle 72h taxation and auto-freezing."""
        now = datetime.datetime.now(datetime.timezone.utc)
        threads = db.query(Thread).filter(Thread.status.in_(["ACTIVE", "OPEN"])).all()
        
        for t in threads:
            try:
                created_at = datetime.datetime.fromisoformat(t.created)
                age = now - created_at
                
                # Rule: After 72h, tax 1 pt every 4h
                if age.total_seconds() > (72 * 3600):
                    last_check = datetime.datetime.fromisoformat(t.last_tax_check) if t.last_tax_check else created_at
                    unaccounted_seconds = (now - last_check).total_seconds()
                    
                    blocks = int(unaccounted_seconds // (4 * 3600))
                    if blocks >= 1:
                        tax = blocks 
                        t.budget -= tax
                        t.last_tax_check = now.isoformat()
                        
                        db.add(Message(thread_id=t.id, who="SYSTEM", what=f"💸 Time Tax: Thread budget reduced by {tax} points.", points=-tax))
                        
                        await self.log(db, "POINT", "SYSTEM", "THREAD_TAX", {
                            "thread": t.id, "amount": tax, "balance_after": t.budget
                        }, dept_id=t.owner_department_id)
                        
                        if t.budget <= 0:
                            t.budget = 0
                            t.status = "FROZEN"
                            db.add(Message(thread_id=t.id, who="SYSTEM", what="⚠️ Thread frozen due to insufficient budget."))
            except Exception:
                pass

    async def deduct_points(self, db, agent, amount: int, reason: str):
        """Helper to deduct points from department or agent wallet. Priority: Dept > Wallet."""
        dept = agent.department
        if dept and dept.ledger_current >= amount:
            dept.ledger_current -= amount
            db.add(LogLedger(department_id=dept.id, who=agent.id, why=reason, amount=-amount))
            await self.log(db, "POINT", "AGENT", "TOOL_COST_DEPT", {
                "agent": agent.name_id, "amount": -amount, "dept": dept.name, "balance_after": dept.ledger_current
            }, agent_id=agent.id, dept_id=dept.id)
            return True
        elif agent.wallet_current >= amount:
            agent.wallet_current -= amount
            await self.log(db, "POINT", "AGENT", "TOOL_COST_WALLET", {
                "agent": agent.name_id, "amount": -amount, "wallet_after": agent.wallet_current
            }, agent_id=agent.id)
            return True
        return False

    # ── Tool handler ─────────────────────────────────────────────────────────

    async def handle_tools(self, db, agent, text: str):
        """Parses [CALL_TOOL]...[END_CALL_TOOL] blocks, executes them, and replaces them in-situ."""
        processed_text = text
        summary = ""
        
        # Find all blocks including tags
        pattern = r"\[CALL_TOOL\](.*?)\[END_CALL_TOOL\]"
        matches = list(re.finditer(pattern, text, re.DOTALL))
        
        if not matches:
            return text, None

        # Replace from end to start to keep indices valid
        for m in reversed(matches):
            full_block = m.group(0)
            inner = m.group(1)
            
            lines = [l.strip() for l in inner.strip().split("\n") if l.strip()]
            if not lines: continue
            
            tool_name = lines[0]
            if tool_name.startswith("- "): tool_name = tool_name[2:].strip()
            
            # ── Charge for tool call ──────────────────────────────────────────
            success = await self.deduct_points(db, agent, 1, f"tool:{tool_name}")
            if not success:
                result = "INSUFFICIENT_FUNDS"
                result_str = f"\n\n> **TOOL ERROR**: `{tool_name}` -> {result}\n\n"
                processed_text = processed_text[:m.start()] + result_str + processed_text[m.end():]
                summary = f"{tool_name}: {result}\n" + summary
                # Stop processing further tools in this tick if bankrupt
                break

            args = []
            for line in lines[1:]:
                if line.startswith("- "):
                    args.append(line[2:].strip().strip('"').strip("'"))
                else:
                    args.append(line.strip().strip('"').strip("'"))

            result = await self.execute_tool_logic(db, agent, tool_name, args)
            
            result_str = f"\n\n> **TOOL RESULT**: `{tool_name}` -> {result}\n\n"
            processed_text = processed_text[:m.start()] + result_str + processed_text[m.end():]
            summary = f"{tool_name}: {result}\n" + summary
            
        return processed_text, summary

    async def execute_tool_logic(self, db, agent, tool_name, args):
        result = "UNKNOWN_TOOL"
        
        # ── modify_own_tick ────────────────────────────────────────────────────
        if tool_name == "modify_own_tick":
            try:
                new_val = int(args[0]) if args else 60
                agent.ticks = new_val
                result = f"CLOCK_SYNC: Tick adjusted to {new_val}s."
            except: result = "CLOCK_ERROR"

        # ── get_time ──────────────────────────────────────────────────────────
        elif tool_name == "get_time":
            result = f"TIME: {datetime.datetime.now().strftime('%H:%M:%S')}"

        # ── create_thread ──────────────────────────────────────────────────────
        elif tool_name == "create_thread":
            if len(args) < 2: return "THREAD_ERROR: Missing topic/aim."
            topic, aim = args[0], args[1]
            ticket_id = args[2].upper() if len(args) > 2 else None
            
            cost = 100 if aim.lower() != "memo" else 25
            ticket_points = 0
            
            if ticket_id:
                ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.status == "UNUSED").first()
                if not ticket: return f"THREAD_ERROR: Ticket {ticket_id} not found or already used."
                ticket_points = ticket.amount
                ticket.status = "USED"
                ticket.used_by = agent.id

            if agent.wallet_current < cost: return "THREAD_ERROR: Insufficient funds."
            
            tid = str(uuid.uuid4())[:8].upper()
            t = Thread(
                id=tid, topic=topic, aim=aim, owner_agent_id=agent.id,
                owner_department_id=agent.department_id, 
                budget=cost + ticket_points, 
                total_invested=cost + ticket_points, 
                status="OPEN",
                last_tax_check=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ticket_id=ticket_id,
                ticket_value=ticket_points
            )
            agent.wallet_current -= cost
            db.add(t)
            
            start_msg = f"🚀 {agent.name_id} started this thread with an initial investment of {cost} points."
            if ticket_id:
                start_msg += f"\n🎟️ This thread was opened with ticket {ticket_id} worth {ticket_points} points."
            
            db.add(Message(thread_id=tid, who=agent.id, what=start_msg, points=cost + ticket_points))
            result = f"THREAD_CREATED: {tid}"

        # ── invest_thread ──────────────────────────────────────────────────────
        elif tool_name == "invest_thread":
            if len(args) < 2: return "INVEST_ERROR: Missing ID/amount."
            tid, amount = args[0].upper(), int(args[1])
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t: return "INVEST_ERROR: Thread not found."
            if agent.wallet_current < amount: return "INVEST_ERROR: Insufficient funds."
            
            is_owner = t.owner_agent_id == agent.id
            is_collab = db.query(ThreadCollaborator).filter(ThreadCollaborator.thread_id == tid, ThreadCollaborator.agent_id == agent.id).first() is not None
            if not (is_owner or is_collab): return "INVEST_ERROR: Not a collaborator."
            
            agent.wallet_current -= amount
            t.budget += amount
            t.total_invested += amount
            db.add(Message(thread_id=tid, who=agent.id, what=f"💰 {agent.name_id} invested {amount} points.", points=amount))
            result = "INVEST_SUCCESS"

        # ── join_thread ────────────────────────────────────────────────────────
        elif tool_name == "join_thread":
            tid, offer = args[0].upper(), int(args[1])
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t: return "JOIN_ERROR"
            if agent.wallet_current < offer: return "JOIN_ERROR: Insufficient funds."
            agent.wallet_current -= offer
            db.add(JoinQuest(thread_id=tid, agent_id=agent.id, offer_points=offer))
            db.add(Message(thread_id=tid, who=agent.id, what=f"🤝 {agent.name_id} requested to join with {offer} points offer."))
            result = "JOIN_REQUESTED"

        # ── approve_join ───────────────────────────────────────────────────────
        elif tool_name == "approve_join":
            tid, joiner_id = args[0].upper(), args[1].upper()
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t or t.owner_agent_id != agent.id: return "AUTH_ERROR"
            quest = db.query(JoinQuest).filter(JoinQuest.thread_id == tid, JoinQuest.agent_id == joiner_id, JoinQuest.status=="PENDING").first()
            if not quest: return "QUEST_NOT_FOUND"
            quest.status = "APPROVED"
            db.add(ThreadCollaborator(thread_id=tid, agent_id=joiner_id))
            t.budget += quest.offer_points
            t.total_invested += quest.offer_points
            db.add(Message(thread_id=tid, who=agent.id, what=f"✅ {agent.name_id} approved {joiner_id}'s join quest.", points=quest.offer_points))
            result = "JOIN_APPROVED"

        # ── post_in_thread ─────────────────────────────────────────────────────
        elif tool_name == "post_in_thread":
            tid, content = args[0].upper(), args[1]
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t or t.status == "FROZEN": return "THREAD_UNAVAILABLE"
            
            is_owner = t.owner_agent_id == agent.id
            is_collab = db.query(ThreadCollaborator).filter(ThreadCollaborator.thread_id == tid, ThreadCollaborator.agent_id == agent.id).first() is not None
            ceo = db.query(Agent).filter(Agent.department_id == t.owner_department_id, Agent.is_ceo == True).first()
            is_superior = (ceo and ceo.id == agent.id)

            if is_owner: cost = 0
            elif is_collab or is_superior: cost = 1
            else: return "AUTH_ERROR: Join first."

            if t.budget < cost: return "INSUFFICIENT_FUNDS"
            t.budget -= cost
            db.add(Message(thread_id=tid, who=agent.id, what=content, points=-cost if cost > 0 else 0))
            result = "POST_SUCCESS"

        # ── set_thread_status ──────────────────────────────────────────────────
        elif tool_name == "set_thread_status":
            tid, status = args[0].upper(), args[1].upper()
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t or t.owner_agent_id != agent.id: return "AUTH_ERROR"
            
            penalty_msg = ""
            if status == "OPEN":
                if agent.wallet_current < 2: return "INSUFFICIENT_FUNDS"
                agent.wallet_current -= 2
                t.status = "OPEN"
            elif status == "REJECT":
                t.status = "REJECTED"
                t.budget = 0
                if t.ticket_id:
                    penalty = t.ticket_value * 5
                    dept = t.owner_department
                    if dept:
                        dept.ledger_current -= penalty
                        db.add(LogLedger(department_id=dept.id, who=agent.id, why=f"Ticket Rejection Penalty ({t.ticket_id})", amount=-penalty))
                        penalty_msg = f"\n⚠️ **PENALTY**: Ticket thread rejected. {penalty} points deducted from {dept.id} ledger."
            else: t.status = status
            
            db.add(Message(thread_id=tid, who=agent.id, what=f"⚙️ Status updated to {status}{penalty_msg}"))
            result = "STATUS_UPDATED"

        # ── guest_invite ──────────────────────────────────────────────────────
        elif tool_name == "invite_to_thread":
            tid, invitee_name, offer = args[0].upper(), args[1], int(args[2])
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t: return "THREAD_NOT_FOUND"
            
            # Auth: only owner or collab can invite
            is_owner = t.owner_agent_id == agent.id
            is_collab = db.query(ThreadCollaborator).filter(ThreadCollaborator.thread_id == tid, ThreadCollaborator.agent_id == agent.id).first() is not None
            if not (is_owner or is_collab): return "AUTH_ERROR"

            if t.budget < offer: return "INSUFFICIENT_FUNDS"
            
            # Find invitee
            invitee = db.query(Agent).filter(Agent.name_id == invitee_name).first()
            if not invitee: return "AGENT_NOT_FOUND"

            # Deduct from thread budget immediately
            t.budget -= offer
            
            # Expiry: +24h
            expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
            expiry_str = expiry.strftime("%m/%d/%y at %I:%M %p") # Format: 02/12/26 at 11:44 PM
            
            db.add(JoinQuest(
                thread_id=tid, agent_id=invitee.id, offer_points=offer, 
                is_invite=True, expires_at=expiry.isoformat()
            ))
            
            # Message according to request
            msg_content = f"Invitation sent to {invitee_name} for {offer} points. Current ledger points are {t.budget} points. Offer expires {expiry_str}"
            db.add(Message(thread_id=tid, who=agent.id, what=msg_content, points=-offer))
            result = f"INVITE_SENT: {invitee_name}"

        # ── accept_invite ──────────────────────────────────────────────────────
        elif tool_name == "accept_invite":
            tid = args[0].upper()
            quest = db.query(JoinQuest).filter(
                JoinQuest.thread_id == tid, 
                JoinQuest.agent_id == agent.id, 
                JoinQuest.status == "PENDING",
                JoinQuest.is_invite == True
            ).first()
            if not quest: return "NO_PENDING_INVITE"

            quest.status = "ACCEPTED"
            # Award points to agent
            agent.wallet_current += quest.offer_points
            # Join as collaborator
            db.add(ThreadCollaborator(thread_id=tid, agent_id=agent.id))
            
            db.add(Message(thread_id=tid, who=agent.id, what=f"✅ {agent.name_id} accepted the invitation. Status: {{invitation_status}}"))
            result = "INVITE_ACCEPTED"

        # ── decline_invite ─────────────────────────────────────────────────────
        elif tool_name == "decline_invite":
            tid = args[0].upper()
            quest = db.query(JoinQuest).filter(
                JoinQuest.thread_id == tid, 
                JoinQuest.agent_id == agent.id, 
                JoinQuest.status == "PENDING",
                JoinQuest.is_invite == True
            ).first()
            if not quest: return "NO_PENDING_INVITE"

            quest.status = "DECLINED"
            # Refund to thread
            t = db.query(Thread).filter(Thread.id == tid).first()
            if t: t.budget += quest.offer_points
            
            db.add(Message(thread_id=tid, who=agent.id, what=f"❌ {agent.name_id} declined the invitation. Status: {{invitation_status}}", points=quest.offer_points))
            result = "INVITE_DECLINED"

        # ── refill_thread ──────────────────────────────────────────────────────

        # ── get_news ──────────────────────────────────────────────────────────
        elif tool_name == "get_news":
            try:
                topic = args[0] if args else "world"
                if topic.lower() in ("world", "general", ""):
                    rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
                else:
                    rss_url = (
                        f"https://news.google.com/rss/search"
                        f"?q={topic}&hl=en-US&gl=US&ceid=US:en"
                    )
                async with httpx.AsyncClient() as client:
                    resp = await client.get(rss_url, timeout=12.0, follow_redirects=True)
                from xml.etree import ElementTree as ET
                root = ET.fromstring(resp.text)
                items = root.findall(".//item")[:4]
                headlines = []
                for item in items:
                    t_el = item.find("title")
                    if t_el is not None and t_el.text:
                        h = re.sub(r"\s*-\s*[^-]+$", "", t_el.text).strip()
                        if h: headlines.append(h)
                result = f"NEWS({topic}): " + " | ".join(headlines) if headlines else "No headlines found."
            except Exception as e: result = f"NEWS_ERROR: {str(e)}"

        # ── get_weather ───────────────────────────────────────────────────────
        elif tool_name == "get_weather":
            city = args[0] if args else "Casablanca"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"https://wttr.in/{city}?format=3", timeout=10.0)
                    result = f"WEATHER: {resp.text.strip()}"
            except Exception as e: result = f"WEATHER_ERROR: {str(e)}"

        # ── get_threads ────────────────────────────────────────────────────────
        elif tool_name == "get_threads":
            try:
                f_status = args[0].strip().upper() if len(args) > 0 and args[0].strip().lower() != "none" else None
                f_dept   = args[1].strip().upper() if len(args) > 1 and args[1].strip() else None
                f_owner  = args[2].strip().upper() if len(args) > 2 and args[2].strip() else None
                
                q = db.query(Thread)
                if f_status: q = q.filter(Thread.status == f_status)
                if f_dept:   q = q.filter(Thread.owner_department_id == f_dept)
                if f_owner:  q = q.filter(Thread.owner_agent_id == f_owner)
                
                threads = q.order_by(Thread.created.desc()).limit(20).all()
                if not threads:
                    result = "THREADS_LIST: No threads matching filters."
                else:
                    lines = [f"{t.id} | {t.topic} | {t.aim} | {t.budget}pt | {t.status}" for t in threads]
                    result = "THREADS_LIST:\n" + "\n".join(lines)
            except Exception as e: result = f"THREADS_ERROR: {str(e)}"

        # ── get_agents ────────────────────────────────────────────────────────
        elif tool_name == "get_agents":
            try:
                f_dept = args[0].strip().upper() if len(args) > 0 and args[0].strip().lower() != "none" else None
                q = db.query(Agent)
                if f_dept: q = q.filter(Agent.department_id == f_dept)
                agents = q.limit(50).all()
                lines = [f"{a.id} | {a.name_id} | {a.department_id} | Wallet: {a.wallet_current}pt" for a in agents]
                result = "AGENTS_LIST:\n" + "\n".join(lines)
            except Exception as e: result = f"AGENTS_ERROR: {str(e)}"

        # ── delete_message ─────────────────────────────────────────────────────
        elif tool_name == "delete_message":
            try:
                tid, mid = args[0].upper(), int(args[1])
                t = db.query(Thread).filter(Thread.id == tid).first()
                if not t or t.owner_agent_id != agent.id: return "AUTH_ERROR"
                msg = db.query(Message).filter(Message.id == mid, Message.thread_id == tid).first()
                if msg:
                    db.delete(msg)
                    result = "MESSAGE_DELETED"
                else: result = "MESSAGE_NOT_FOUND"
            except Exception as e: result = f"DELETE_ERROR: {str(e)}"

        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def deduct_points(self, db: Session, agent: Agent, amount: int, why: str):
        """Standard point deduction from Dept or Wallet."""
        dept = agent.department
        if dept and dept.ledger_current >= amount:
            dept.ledger_current -= amount
            db.add(LogLedger(department_id=dept.id, who=agent.id, why=why, amount=-amount))
            return True
        if agent.wallet_current >= amount:
            agent.wallet_current -= amount
            return True
        return False

    async def handle_quest_expirations(self, db: Session):
        """Find pending invites that passed 24h and refund thread budget."""
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        expired = db.query(JoinQuest).filter(
            JoinQuest.status == "PENDING",
            JoinQuest.is_invite == True,
            JoinQuest.expires_at < now_str
        ).all()
        
        for q in expired:
            q.status = "EXPIRED"
            t = db.query(Thread).filter(Thread.id == q.thread_id).first()
            if t:
                t.budget += q.offer_points
                db.add(Message(thread_id=t.id, who="SYSTEM", what=f"⚠️ Invitation for {q.agent_id} expired. {q.offer_points} pts refunded to budget.", points=q.offer_points))
            await self.log(db, "INFO", "SYSTEM", "INVITE_EXPIRED", {"agent": q.agent_id, "thread": q.thread_id})
        
        if expired: db.commit()

    def get_rich_invitation_context(self, db: Session, agent: Agent):
        """Builds a formatted list of invitations with full metadata."""
        invites = db.query(JoinQuest).filter(
            JoinQuest.agent_id == agent.id,
            JoinQuest.status == "PENDING",
            JoinQuest.is_invite == True
        ).all()
        
        if not invites: return "No pending invitations."
        
        lines = []
        for q in invites:
            t = db.query(Thread).filter(Thread.id == q.thread_id).first()
            if not t: continue
            lines.append(
                f"- THREAD_ID: {t.id} | TOPIC: {t.topic} | OWNER: {t.owner_agent_id} | "
                f"AIM: {t.aim} | THREAD_BUDGET: {t.budget}pt | OFFER: {q.offer_points}pt | "
                f"EXPIRES: {q.expires_at}"
            )
            q.is_read = True # Mark as read when contextualized
        return "\n".join(lines)

    def get_available_tickets_context(self, db: Session):
        """Builds a formatted list of UNUSED tickets."""
        tickets = db.query(Ticket).filter(Ticket.status == "UNUSED").all()
        if not tickets: return "No tickets currently available."
        
        lines = []
        for t in tickets:
            lines.append(
                f"-- {t.name}\n"
                f"-- {t.amount} pts\n"
                f"-- {t.id}"
            )
        return "\n".join(lines)

engine = SimEngine()
