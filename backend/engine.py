import asyncio
import httpx
import datetime
import json
import re
import traceback
import uuid
import random
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    Agent, Thread, LogAction, LogLedger, Department,
    Setting, AgentTool, SystemLog,
    ThreadCollaborator, JoinQuest, Message, Ticket,
    Transaction, ToolOwnership, AgentPrompt
)

# Legacy hardcoded tool lists removed in favour of dynamic Tool model injection.


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

    def get_quest_tools(self, db: Session):
        quest_tools = db.query(AgentTool).filter(AgentTool.enabled == True).all()
        
        tools_block = (
            "\n".join([f"- {t.description}" for t in quest_tools if t.id in ["approve_join", "decline_join"]])
            if quest_tools else "No tools currently available."
        )
        return tools_block

    def get_tools(self, db: Session):
        enabled_tools = db.query(AgentTool).filter(AgentTool.enabled == True).all()
        tools_block = (
            "\n".join([f"- {t.description}" for t in enabled_tools])
            if enabled_tools else "No tools currently available."
        )
        return tools_block
    
    def get_filter_tools(self, db: Session, lst=[]):
        enabled_tools = db.query(AgentTool).filter(AgentTool.enabled == True, AgentTool.id.in_(lst)).all()
        tools_block = (
            "\n".join([f"- {t.description}" for t in enabled_tools])
            if enabled_tools else "No tools currently available."
        )
        return tools_block
        

    async def tick(self):
        self.counter += 1
        if self.counter >= 3600:
            self.counter = 0

        db: Session = SessionLocal()
        try:
            agents = db.query(Agent).all()
            ticking_agents = [a for a in agents if not a.is_halted and a.ticks > 0 and self.counter % a.ticks == 0]
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
                agent_tools_prompt = f"\nACTIVE THREADS:\n{t_context}"

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
        run_steps = []
        def add_step(stype, content, metadata=None):
            run_steps.append({
                "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "type": stype,
                "content": content,
                "metadata": metadata or {}
            })

        add_step("system", "Tick started")
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent: return

            # Initial Point Deduction (occurred in tick() before this call)
            s_halt = db.query(Setting).filter(Setting.key == "llm_halt").first()
            if not s_halt or s_halt.value != "true":
                add_step("wallet", "Tick starting (1 pt cost)", {"amount": -1, "reason": "tick"})

            # 2. Context
            # Find last quest for status placeholder
            last_q = db.query(JoinQuest).filter(JoinQuest.agent_id == agent.id).order_by(JoinQuest.id.desc()).first()

            # Last actions
            actions = db.query(LogAction).filter(LogAction.agent_id == agent.id).order_by(LogAction.id.desc()).limit(5).all()
            actions_str = "\n".join([f"- {a.what} ({a.points} pts)" for a in actions]) if actions else "No recent actions."

            # SUM UP RECENT AGENT ACTIONS
            SYSTEM_PROMPT_SUMMER = """
            You are a "Memory Summer" for an AI agent. 
            Sum up this agent's recent actions in less than 50 words.
            Speak as the agent using words like "I".
            Focus on his last actions, and provide insight on what he should do next if any. Be short and on point. KEEP key information such as ID.

            INPUT:
            Recent Actions (last 5).

            OUTPUT FORMAT
            Return the summary in less than 50 words.
            """

            USER_PROMPT_SUMMER = f"""
            {actions_str}
            """

            # 3. Call LLM
            s_url = db.query(Setting).filter(Setting.key == "ollama_server").first()
            s_mod = db.query(Setting).filter(Setting.key == "ollama_model").first()
            s_timeout = db.query(Setting).filter(Setting.key == "llm_timeout").first()
            server = s_url.value if s_url else "http://localhost:11434"
            model  = s_mod.value if s_mod else "gemma4:e4b"
            timeout_val = float(s_timeout.value) if s_timeout else 1500.0

            # CONTINUE
            final_processed_raw = ""
            dept_info = f"Department: {agent.department.name} (Balance: {agent.department.ledger_current} pts)" if agent.department else "No Department"
            
            # Fetch prompt for the current mode
            cur_mode = agent.mode or "Custom"
            ap = db.query(AgentPrompt).filter(AgentPrompt.agent_id == agent.id, AgentPrompt.mode == cur_mode).first()
            if not ap:
                # Fallback to any prompt or default
                ap = db.query(AgentPrompt).filter(AgentPrompt.agent_id == agent.id).first()

            system_prompt_raw = ap.system_prompt if ap else agent.system_prompt or ""
            user_prompt_raw = ap.user_prompt if ap else agent.user_prompt or ""
            system_prompt = ""
            user_prompt = ""
            full_tool_results=""
            if s_halt and s_halt.value == "true":
                import uuid
                final_processed_raw = "LLM CALLS HALTED IN SETTINGS."
                add_step("system", "LLM calls are halted via settings.")
                await self.log(db, "INFO", "AGENT", "LLM_HALTED", {"agent": agent.name_id}, agent_id=agent.id, dept_id=agent.department_id)
                action_snippet = "Agent loop skipped. LLM halted."
                db.add(LogAction(agent_id=agent.id, what=action_snippet, points=0))
                run_id = str(uuid.uuid4())[:8].upper()
                await self.broadcast({
                    "type": "run",
                    "run": {
                        "id": run_id,
                        "agent": agent.name_id,
                        "agent_id": agent.id,
                        "dept": agent.department_id,
                        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "msg": action_snippet,
                        "steps": run_steps
                    }
                })
                db.commit()
            else:
                add_step("system", f"AI session starting (Timeout: {int(timeout_val)}s)")
                async with httpx.AsyncClient() as client:
                    # 3a. Generate memory summary
                    add_step("system", "Generating memory summary")
                    resp = await client.post(
                        f"{server}/api/generate",
                        json={
                            "model": "gemma4:e4b",
                            "system": SYSTEM_PROMPT_SUMMER,
                            "prompt": USER_PROMPT_SUMMER,
                            "stream": False
                        },
                        timeout=360.0
                    )
                    raw_summary = resp.json().get("response", "")
                    actions_str = raw_summary
                    
                    
                    # s_prefix = db.query(Setting).filter(Setting.key == "tools_instruction_prefix").first()
                    # tools_block = (s_prefix.value + "\n" if s_prefix else "AVAILABLE TOOLS:\n") + self.get_tools(db)
                    tools_block = self.get_tools(db)

                    extra_ctx = {
                        "actions": actions_str,
                        "tools": tools_block,
                    }
                    
                    user_prompt = await self.resolve_placeholders(user_prompt_raw, db, agent, last_q, add_step, extra_ctx=extra_ctx)
                    system_prompt = await self.resolve_placeholders(system_prompt_raw, db, agent, last_q, add_step, extra_ctx=extra_ctx)
                    
                    add_step("thought", "Thinking...", {"system_prompt": system_prompt, "user_prompt": user_prompt})
                    
                    MAX_ITERATIONS = 10
                    current_user_prompt = user_prompt
                    final_processed_raw = ""
                    full_tool_results = None
                    
                    for iter_count in range(MAX_ITERATIONS):
                        add_step("iteration", f"Iteration {iter_count + 1} / {MAX_ITERATIONS}")
                        resp = await client.post(
                            f"{server}/api/generate",
                            json={
                                "model": model,
                                "system": system_prompt,
                                "prompt": current_user_prompt,
                                "stream": False,
                                "options": {
                                    "temperature": 0.7,   # Adjust for creativity vs. logic
                                    "num_predict": 4096,  # Ensure it doesn't cut off mid-thought
                                    "top_p": 0.9,
                                }
                            },
                            timeout=timeout_val
                        )
                        raw = resp.json().get("response", "")
                    
                        print(f"Agent {agent.id} (Iter {iter_count+1}) raw response:\n", raw)
                        add_step("response", f"Response received (Iter {iter_count+1})", {"raw": raw})
                        
                        # 4. Handle State [MEMORY]...[END MEMORY] and [MODE]...[END MODE]
                        mem_match = re.search(r"\[MEMORY\](.*?)\s*\[END MEMORY\]", raw, re.DOTALL | re.IGNORECASE)
                        mode_match = re.search(r"\[MODE\](.*?)\s*\[END MODE\]", raw, re.DOTALL | re.IGNORECASE)
                        if mem_match:
                            agent.memory = mem_match.group(1).strip()[:200]
                            raw = raw.replace(mem_match.group(0), "").strip()
                            add_step("memory", f"Memory Updated", {"content": agent.memory})

                        if mode_match:
                            next_val = mode_match.group(1).strip()
                            def normalize_mode(m):
                                m_low = m.lower().strip().replace("_", " ")
                                if "creator" in m_low: return "Creator"
                                if "investor" in m_low: return "Investor"
                                if "points" in m_low: return "Points Accounter"
                                if "custom" in m_low: return "Custom"
                                return None
                            
                            norm_mode = normalize_mode(next_val)
                            if norm_mode:
                                agent.next_mode = norm_mode
                                add_step("system", f"Mode change queued: {norm_mode}")
                            raw = raw.replace(mode_match.group(0), "").strip()

                        # 5. Handle Tools
                        processed_raw, iter_tool_results = await self.handle_tools(db, agent, raw, add_step)
                        
                        final_processed_raw += processed_raw + "\n"
                        
                        if iter_tool_results:
                            if full_tool_results is None:
                                full_tool_results = ""
                            full_tool_results += iter_tool_results + "\n"
                            
                            # Check if agent's department has enough points to continue
                            dept = agent.department
                            if dept and dept.ledger_current >= 1 and iter_count < MAX_ITERATIONS - 1:
                                # Tax 1 pt from agent's department
                                dept.ledger_current -= 1
                                db.add(LogLedger(department_id=dept.id, who=agent.id, why="thinking_iteration_tax", amount=-1))
                                add_step("wallet", "Thinking Iteration Tax: -1 pt", {"amount": -1, "reason": "thinking_iteration_tax"})
                                
                                prompt_continuation = (
                                    f"\n\nAssistant:\n{processed_raw}\n\nSystem (Tool Results):\n{iter_tool_results}\n\n"
                                    f"You can either continue your turn based on these tool results or you can stop. (Tax of 1 point was deducted from your department to continue). "
                                    f"Your department has {dept.ledger_current} points remaining.\n"
                                    "Call another tool if needed, otherwise provide your final reply."
                                )
                                current_user_prompt += prompt_continuation
                                add_step("system", "Continuing to next iteration")
                            else:
                                if iter_count < MAX_ITERATIONS - 1:
                                    add_step("system", "Iteration stopped due to insufficient department points or no dept.")
                                break
                        else:
                            break
                    
                    # 5b. Force Mode if missing
                    if not agent.next_mode:
                        add_step("system", "Asking for Mode (Final Round)")
                        mode_prompt_system = (
                            "You have finished your turn. Now you must decide your NEXT MODE for the next tick.\n"
                            "Available modes: Creator, Points Accounter, Investor.\n"
                            "Please provide it in the format:\n"
                            "[MODE]\n"
                            "NEXT MODE\n"
                            "[END MODE]"
                        )
                        mode_prompt_user = "[MODE]\nNEXT MODE\n[END MODE]"
                        
                        resp = await client.post(
                            f"{server}/api/generate",
                            json={
                                "model": model,
                                "system": mode_prompt_system,
                                "prompt": mode_prompt_user,
                                "stream": False,
                                "options": {
                                    "temperature": 0.3,
                                    "num_predict": 100,
                                }
                            },
                            timeout=timeout_val
                        )
                        mode_raw = resp.json().get("response", "")
                        add_step("response", "Mode response received", {"raw": mode_raw})
                        
                        m_match = re.search(r"\[MODE\](.*?)\s*\[END MODE\]", mode_raw, re.DOTALL | re.IGNORECASE)
                        if m_match:
                            m_val = m_match.group(1).strip()
                            def normalize_mode_final(m):
                                m_low = m.lower().strip().replace("_", " ")
                                if "creator" in m_low: return "Creator"
                                if "investor" in m_low: return "Investor"
                                if "points" in m_low: return "Points Accounter"
                                return None
                            norm_m = normalize_mode_final(m_val)
                            if norm_m:
                                agent.next_mode = norm_m
                                add_step("system", f"Mode determined: {norm_m}")
                            else:
                                add_step("system", "Mode normalization failed or unrecognized mode.")
                        else:
                            add_step("system", "Format error in mode response.")
                
            # 6. Final Logic: Log Action
            action_snippet = final_processed_raw[:250] + ("..." if len(final_processed_raw) > 250 else "")
            db.add(LogAction(agent_id=agent.id, what=action_snippet, points=0))
            
            # Prepare rich details for System Logger
            prompt_preview = f"SYSTEM:\n{system_prompt[:200]}...\n\nUSER:\n{user_prompt[:200]}..."
            response_preview = final_processed_raw

            await self.log(db, "INFO", "AGENT", "TICK_COMPLETE", {
                "agent": agent.name_id,
                "prompt_preview": prompt_preview,
                "response_preview": response_preview,
                "action": action_snippet,
                "tool_results": full_tool_results
            }, agent_id=agent.id, dept_id=agent.department_id)

            add_step("complete", "Tick complete")

            # 7. Broadcast to Activity Feed (Restructured as Run)
            import uuid
            run_id = str(uuid.uuid4())[:8].upper()
            await self.broadcast({
                "type": "run",
                "run": {
                    "id": run_id,
                    "agent": agent.name_id,
                    "agent_id": agent.id,
                    "dept": agent.department_id,
                    "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "msg": action_snippet,
                    "steps": run_steps
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

    async def deduct_points(self, db, agent, amount: int, reason: str, add_step_cb=None):
        """Helper to deduct points from department or agent wallet. Priority: Dept > Wallet."""
        # get department of the agent
        dept = db.query(Department).filter(Department.id == agent.department_id).first()
        success = False
        if dept and dept.ledger_current >= amount:
            dept.ledger_current -= amount
            db.add(LogLedger(department_id=dept.id, who=agent.id, why=reason, amount=-amount))
            await self.log(db, "POINT", "AGENT", f"DEDUCT_{reason.upper()}_DEPT", {
                "agent": agent.name_id, "amount": -amount, "dept": dept.name, "balance_after": dept.ledger_current, "reason": reason
            }, agent_id=agent.id, dept_id=dept.id)
            if add_step_cb:
                add_step_cb("wallet", f"Deducted {amount} pt from Department ({reason})", {"amount": -amount, "reason": reason, "source": "dept"})
            success = True
        elif agent.wallet_current >= amount:
            agent.wallet_current -= amount
            await self.log(db, "POINT", "AGENT", f"DEDUCT_{reason.upper()}_WALLET", {
                "agent": agent.name_id, "amount": -amount, "wallet_after": agent.wallet_current, "reason": reason
            }, agent_id=agent.id)
            if add_step_cb:
                add_step_cb("wallet", f"Deducted {amount} pt from Wallet ({reason})", {"amount": -amount, "reason": reason, "source": "wallet"})
            success = True
        return success

    # ── Tool handler ─────────────────────────────────────────────────────────

    async def handle_tools(self, db, agent, text: str, add_step_cb=None):
        """Parses */ blocks generated by the LLM and executes them via the central router."""
        processed_text = text
        summary = ""
        
        pattern = r"\*/(.*?)/\*"
        matches = list(re.finditer(pattern, text, re.DOTALL))
        
        if not matches:
            return text, None

        for m in reversed(matches):
            inner = m.group(1)
            parts = [p.strip() for p in inner.split("|") if p.strip()]
            if not parts: continue
            
            tool_name = parts[0]
            args = parts[1:]

            # Hand off to the exact same execution logic that parses inline prompt commands!
            if add_step_cb:
                add_step_cb("tool_call", f"Calling {tool_name}", {"tool": tool_name, "args": args})
            
            result = await self._execute_inline_command(tool_name, args, db, agent, add_step_cb)
            
            if add_step_cb:
                add_step_cb("tool_result", f"Result for {tool_name}", {"tool": tool_name, "result": result})
            
            # Formatting the result back into the text
            result_str = f"\n\n> **TOOL RESULT**: `{tool_name}` -> {result}\n\n"
            processed_text = processed_text[:m.start()] + result_str + processed_text[m.end():]
            summary = f"{tool_name}: {result[:50]}\n" + summary
            
            # Stop processing further tools if we hit a bankruptcy flag from the executor
            if "INSUFFICIENT_FUNDS" in result or "TOOL_NO_FUNDS" in result:
                break
            
        return processed_text, summary

    async def execute_tool_logic(self, db, agent, tool_name, args, add_step_cb=None):
        result = "UNKNOWN_TOOL"
        tool_name = tool_name.lower().strip()
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
            
            base_cost = 100 if aim.lower() != "memo" else 25
            ticket_points = 0
            
            if ticket_id:
                ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.status == "UNUSED").first()
                if not ticket: return f"THREAD_ERROR: Ticket {ticket_id} not found or already used."
                ticket_points = ticket.amount
                ticket.status = "USED"
                ticket.used_by = agent.id
                actual_wallet_cost = 0 # No mandatory cost if ticket is used
            else:
                if agent.wallet_current < base_cost: return "THREAD_ERROR: Insufficient funds."
                actual_wallet_cost = base_cost

            tid = str(uuid.uuid4())[:8].upper()
            t = Thread(
                id=tid, topic=topic, aim=aim, owner_agent_id=agent.id,
                owner_department_id=agent.department_id, 
                budget=actual_wallet_cost + ticket_points, 
                total_invested=actual_wallet_cost + ticket_points, 
                status="OPEN",
                last_tax_check=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ticket_id=ticket_id,
                ticket_value=ticket_points
            )
            
            if actual_wallet_cost > 0:
                agent.wallet_current -= actual_wallet_cost
                if add_step_cb:
                    add_step_cb("wallet", f"Thread Creation Cost: -{actual_wallet_cost} pts", {"amount": -actual_wallet_cost, "reason": "create_thread", "topic": topic})
                await self.log(db, "POINT", "AGENT", "THREAD_CREATE", {"agent": agent.name_id, "thread_id": tid, "cost": -actual_wallet_cost}, agent_id=agent.id)
            
            db.add(t)
            
            start_msg = f"🚀 {agent.name_id} started this thread"
            if actual_wallet_cost > 0:
                start_msg += f" with an initial investment of {actual_wallet_cost} points."
            else:
                start_msg += "."
                
            if ticket_id:
                start_msg += f"\n🎟️ This thread was opened with ticket {ticket_id} worth {ticket_points} points."
            
            db.add(Message(thread_id=tid, who=agent.id, what=start_msg, points=actual_wallet_cost + ticket_points))
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
            if add_step_cb:
                add_step_cb("wallet", f"Thread Investment: -{amount} pts", {"amount": -amount, "reason": "invest_thread", "thread_id": tid})
            await self.log(db, "POINT", "AGENT", "THREAD_INVEST", {"agent": agent.name_id, "thread_id": tid, "amount": -amount}, agent_id=agent.id)
            db.add(Message(thread_id=tid, who=agent.id, what=f"💰 {agent.name_id} invested {amount} points.", points=amount))
            result = "INVEST_SUCCESS"

        # ── join_thread ────────────────────────────────────────────────────────
        elif tool_name == "join_thread":
            if len(args) < 2: return "JOIN_ERROR: Missing ID/offer."
            if len(args) == 0:
                return "JOIN_ERROR: Missing ID and offer. Syntax is */\n- join_thread\n- thread_id\n- offer_points\n/*"
            elif len(args) == 1:
                tid = args[0].upper().strip()
                offer = 0
                await self.log(db, "INFO", "AGENT",\
                    "THREAD_JOIN_REQUEST NO OFFER POINTS ASSUMED 0. IF YOU WANT TO OFFER POINTS, USE THE FULL SYNTAX.",\
                    {"agent": agent.name_id, "thread_id": tid, "offer": -offer}, agent_id=agent.id)
            else:
                tid, offer = args[0], int(args[1])
            tid = tid.upper().strip()
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t: return "JOIN_ERROR"

            # Ensure thread is OPEN or ACTIVE
            if t.status not in ["OPEN", "ACTIVE"]:
                return f"JOIN_ERROR: Thread {tid} is {t.status} and cannot be joined."

            # VERIFY HE'S NOT THE OWNER OF THE THREAD
            if t.owner_agent_id == agent.id:
                return "JOIN_ERROR: You are the owner of this thread. You can post for free, send invites to others to join, or invest in it."

            # Check for existing pending join request (agent-initiated)
            existing_quest = db.query(JoinQuest).filter(
                JoinQuest.thread_id == tid,
                JoinQuest.agent_id == agent.id,
                JoinQuest.status == "PENDING",
                JoinQuest.is_invite.is_(False)
            ).first()

            if existing_quest:
                if offer > existing_quest.offer_points:
                    # Upgrade offer
                    if agent.wallet_current < offer:
                        return f"JOIN_ERROR: Insufficient funds to raise offer to {offer} P."
                    
                    refund = existing_quest.offer_points
                    agent.wallet_current += refund
                    agent.wallet_current -= offer
                    existing_quest.offer_points = offer
                    
                    if add_step_cb:
                        add_step_cb("wallet", f"Join Offer Raised: +{refund} P (refund), -{offer} P (new)", 
                                    {"refund": refund, "new_offer": offer, "reason": "join_thread_upgrade", "thread_id": tid})
                    
                    await self.log(db, "POINT", "AGENT", "THREAD_JOIN_UPGRADE", 
                                   {"agent": agent.name_id, "thread_id": tid, "old_offer": refund, "new_offer": offer}, 
                                   agent_id=agent.id)
                    
                    db.add(Message(thread_id=tid, who=agent.id, what=f"🤝 {agent.name_id} raised their Join Quest offer to {offer} points."))
                    result = f"THREAD JOIN OFFER NOW RAISED TO {offer} P, WAIT UNTIL REQUEST APPROVAL BEFORE POSTING"
                    # Add info about refund to the result for the agent
                    result += f". {refund} points from previous offer returned."
                    return result
                else:
                    return "YOU ALREADY REQUESTED WITH HIGHER OFFER. WAIT UNTIL REQUEST APPROVAL BEFORE POSTING"

            if agent.wallet_current < offer: return "JOIN_ERROR: Insufficient funds."
            agent.wallet_current -= offer
            if add_step_cb:
                add_step_cb("wallet", f"Join Offer: -{offer} pts", {"amount": -offer, "reason": "join_thread", "thread_id": tid})
            await self.log(db, "POINT", "AGENT", "THREAD_JOIN_REQUEST", {"agent": agent.name_id, "thread_id": tid, "offer": -offer}, agent_id=agent.id)
            db.add(JoinQuest(thread_id=tid, agent_id=agent.id, offer_points=offer))
            db.add(Message(thread_id=tid, who=agent.id, what=f"🤝 {agent.name_id} requested to join with {offer} points offer."))
            result = "JOIN_REQUESTED. WAIT FOR THREAD OWNER TO APPROVE YOUR JOIN QUEST. NO POSTING UNTIL APPROVED."

        # ── approve_join ───────────────────────────────────────────────────────
        elif tool_name == "approve_join":
            tid, joiner_id = args[0].upper(), args[1].upper()
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t or t.owner_agent_id != agent.id: return "AUTH_ERROR"
            # Check if ALREADY approved
            already = db.query(JoinQuest).filter(
                JoinQuest.thread_id == tid, 
                JoinQuest.agent_id == joiner_id, 
                JoinQuest.status=="APPROVED"
            ).first()
            if already:
                tools_now = self.get_tools(db)
                return f"Join quest already approved ! Available tools now: {tools_now}"

            quest = db.query(JoinQuest).filter(JoinQuest.thread_id == tid, JoinQuest.agent_id == joiner_id, JoinQuest.status=="PENDING").first()
            if not quest: return "QUEST_NOT_FOUND"
            quest.status = "APPROVED"
            db.add(ThreadCollaborator(thread_id=tid, agent_id=joiner_id))
            t.budget += quest.offer_points
            t.total_invested += quest.offer_points
            if add_step_cb:
                add_step_cb("wallet", f"Join Approved (Thread Budget): +{quest.offer_points} pts", {"amount": quest.offer_points, "reason": "approve_join", "joiner": joiner_id})
            await self.log(db, "POINT", "AGENT", "THREAD_JOIN_APPROVE", {"agent": agent.name_id, "thread_id": tid, "joiner": joiner_id, "budget_add": quest.offer_points}, agent_id=agent.id)
            db.add(Message(thread_id=tid, who=agent.id, what=f"✅ {agent.name_id} approved {joiner_id}'s join quest.", points=quest.offer_points))
            result = "JOIN_APPROVED"

        # ── decline_join ───────────────────────────────────────────────────────
        elif tool_name == "decline_join":
            tid, joiner_id = args[0].upper(), args[1].upper()
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t or t.owner_agent_id != agent.id: return "AUTH_ERROR"
            quest = db.query(JoinQuest).filter(JoinQuest.thread_id == tid, JoinQuest.agent_id == joiner_id, JoinQuest.status=="PENDING").first()
            if not quest: return "QUEST_NOT_FOUND"
            quest.status = "DECLINED"
            # points should be returned to the joiner (only half)
            joiner = db.query(Agent).filter(Agent.id == joiner_id).first()
            joiner.wallet_current += quest.offer_points // 2
            if add_step_cb:
                add_step_cb("wallet", f"Join Declined (Refund Half): {quest.offer_points // 2} pts returned to {joiner_id}", {"amount": quest.offer_points // 2, "reason": "decline_join", "joiner": joiner_id})
            await self.log(db, "POINT", "AGENT", "THREAD_JOIN_DECLINE", {"agent": agent.name_id, "thread_id": tid, "joiner": joiner_id, "refund": quest.offer_points // 2}, agent_id=agent.id)
            db.add(Message(thread_id=tid, who=agent.id, what=f"✅ {agent.name_id} declined {joiner_id}'s join quest.", points=quest.offer_points))
            result = "JOIN_DECLINED"

        # ── post_in_thread ─────────────────────────────────────────────────────
        elif tool_name == "post_in_thread":
            tid, content = args[0].upper(), "\n".join(args[1:])
            t = db.query(Thread).filter(Thread.id == tid).first()
            if not t: return "THREAD_ERROR: Not found."
            
            if t.status == "FROZEN":
                if t.owner_agent_id == agent.id:
                    return f"THREAD_FROZEN: This thread is frozen due to tax debts. You must reactivate it first using `set_thread_status('{tid}', 'OPEN')` (costs 2 pts)."
                else:
                    return "THREAD_UNAVAILABLE: This thread is currently frozen."
            
            if t.status not in ["OPEN", "ACTIVE"]:
                return f"THREAD_UNAVAILABLE: This thread is {t.status} and no longer accepting posts."
            
            is_owner = t.owner_agent_id == agent.id
            is_collab = db.query(ThreadCollaborator).filter(ThreadCollaborator.thread_id == tid, ThreadCollaborator.agent_id == agent.id).first() is not None
            ceo = db.query(Agent).filter(Agent.department_id == t.owner_department_id, Agent.is_ceo == True).first()
            is_superior = (ceo and ceo.id == agent.id)

            if is_owner: cost = 0
            elif is_collab or is_superior: cost = 1
            else: return "AUTH_ERROR: Join first. Use join_thread tool: join_thread|thread_id|offer_points"

            if t.budget < cost: return "INSUFFICIENT_FUNDS"
            t.budget -= cost
            if add_step_cb and cost > 0:
                add_step_cb("wallet", f"Post Fee: -{cost} pts from thread", {"amount": -cost, "reason": "post_in_thread", "thread_id": tid})
            if cost > 0:
                await self.log(db, "POINT", "AGENT", "THREAD_POST_FEE", {"agent": agent.name_id, "thread_id": tid, "cost": -cost}, agent_id=agent.id)
            db.add(Message(thread_id=tid, who=agent.id, what=content, points=-cost if cost > 0 else 0))
            asyncio.create_task(self.compute_thread_summary(tid))
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
                if add_step_cb:
                    add_step_cb("wallet", "Thread Reactivation Fee: -2 pts", {"amount": -2, "reason": "reactivate_thread", "thread_id": tid})
                await self.log(db, "POINT", "AGENT", "THREAD_OPEN_FEE", {"agent": agent.name_id, "thread_id": tid, "cost": -2}, agent_id=agent.id)
                t.status = "OPEN"
            elif status == "REJECT":
                t.status = "REJECTED"
                t.budget = 0
                if t.ticket_id:
                    penalty = t.ticket_value * 5
                    dept = t.owner_department
                    if dept:
                        dept.ledger_current -= penalty
                        if add_step_cb:
                            add_step_cb("wallet", f"Department Penalty: -{penalty} pts", {"amount": -penalty, "reason": "ticket_rejection", "dept": dept.id})
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
            if add_step_cb:
                add_step_cb("wallet", f"Invite Offer: -{offer} pts from thread", {"amount": -offer, "reason": "invite_to_thread", "invitee": invitee_name})
            await self.log(db, "POINT", "AGENT", "THREAD_INVITE_OFFER", {"agent": agent.name_id, "thread_id": tid, "invitee": invitee_name, "offer": -offer}, agent_id=agent.id)
            
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
            if add_step_cb:
                add_step_cb("wallet", f"Invite Accepted: +{quest.offer_points} pts received", {"amount": quest.offer_points, "reason": "accept_invite", "thread_id": tid})
            await self.log(db, "POINT", "AGENT", "THREAD_INVITE_ACCEPT", {"agent": agent.name_id, "thread_id": tid, "reward": quest.offer_points}, agent_id=agent.id)
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
            if t: 
                t.budget += quest.offer_points
                if add_step_cb:
                    add_step_cb("wallet", f"Invite Declined: +{quest.offer_points} pts refunded to thread", {"amount": quest.offer_points, "reason": "decline_invite", "thread_id": tid})
                await self.log(db, "POINT", "AGENT", "THREAD_INVITE_DECLINE", {"agent": agent.name_id, "thread_id": tid, "refund": quest.offer_points}, agent_id=agent.id)
            
            db.add(Message(thread_id=tid, who=agent.id, what=f"❌ {agent.name_id} declined the invitation. Status: {{invitation_status}}", points=quest.offer_points))
            result = "INVITE_DECLINED"

        # ── stealth_mode_thread ────────────────────────────────────────────────
        elif tool_name == "stealth_mode_thread":
            try:
                tid = args[0].strip().upper() if args else ""
                t = db.query(Thread).filter(Thread.id == tid).first()
                if not t: return f"STEALTH_ERROR: Thread {tid} not found."
                if t.owner_agent_id != agent.id: return "AUTH_ERROR: Only the owner can activate Stealth Mode."
                
                cost = 10
                if agent.wallet_current < cost: return "INSUFFICIENT_FUNDS"
                
                agent.wallet_current -= cost
                t.is_stealth = True
                
                if add_step_cb:
                    add_step_cb("wallet", f"Stealth Mode Activated: -{cost} pts", {"amount": -cost, "reason": "stealth_mode", "thread_id": tid})
                await self.log(db, "POINT", "AGENT", "THREAD_STEALTH", {"agent": agent.name_id, "thread_id": tid, "cost": -cost}, agent_id=agent.id)
                db.add(Message(thread_id=tid, who="SYSTEM", what="🕵️ Thread moved to Stealth Mode.", points=-cost))
                result = "STEALTH_MODE_ACTIVATED"
            except Exception as e: result = f"STEALTH_ERROR: {str(e)}"

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

        # ── web_search ─────────────────────────────────────────────────────────
        elif tool_name == "web_search":
            def contains_any_keyword(text: str, keywords: list[str]) -> bool:
                if not text or not keywords:
                    return False
                
                # What should we do here to handle multi-word phrases safely?
                text_lower = text.lower()
                
                for kw in keywords:
                    if kw.lower() in text_lower:   # Simple but effective for phrases
                        return True
                return False

            try:
                if len(args) < 2:
                    return "WEB_SEARCH_ERROR: Usage: web_search | thread_id | search query"
                tid = args[0].strip().upper()
                query = " ".join(args[1:]).strip()
                if not query:
                    return "WEB_SEARCH_ERROR: Empty search query."

                t = db.query(Thread).filter(Thread.id == tid).first()
                if not t:
                    return f"WEB_SEARCH_ERROR: Thread {tid} not found."

                # Auth: must be owner or collaborator (Founder bypasses)
                is_founder = (agent.id == "FOUNDER")
                is_owner = t.owner_agent_id == agent.id
                is_collab = db.query(ThreadCollaborator).filter(
                    ThreadCollaborator.thread_id == tid,
                    ThreadCollaborator.agent_id == agent.id
                ).first() is not None
                if not (is_owner or is_collab or is_founder):
                    return "WEB_SEARCH_ERROR: Must be owner or collaborator of the thread."

                # Pricing: 10 pts first use in this thread, 30 pts after (Free for Founder)
                if is_founder:
                    cost = 0
                else:
                    prior_searches = db.query(Message).filter(
                        Message.thread_id == tid,
                        Message.who == agent.id,
                        Message.what.like("%🔍 WEB_SEARCH%")
                    ).count()
                    cost = 10 if prior_searches == 0 else 30

                if t.budget < cost:
                    return f"WEB_SEARCH_ERROR: Thread budget insufficient ({t.budget} < {cost} pts needed)."

                t.budget -= cost
                if add_step_cb:
                    add_step_cb("wallet", f"Web Search Fee: -{cost} pts from thread {tid}",
                                {"amount": -cost, "reason": "web_search", "thread_id": tid, "query": query})
                await self.log(db, "POINT", "AGENT", "WEB_SEARCH_FEE",
                               {"agent": agent.name_id, "thread_id": tid, "cost": -cost, "query": query},
                               agent_id=agent.id)

                # ── Step 1: Tavily Search Integration ────────────────────────
                s_tavily = db.query(Setting).filter(Setting.key == "tavily_api_keys").first()
                tavily_keys = [k.strip() for k in re.split(r'[,\n\s]+', s_tavily.value) if k.strip()] if s_tavily else []
                
                if not tavily_keys:
                    return "WEB_SEARCH_ERROR: No Tavily API keys configured in settings."
                
                tavily_key = random.choice(tavily_keys)
                if add_step_cb:
                    add_step_cb("system", f"Using Tavily API Key: {tavily_key[:6]}...{tavily_key[-4:]}")

                final_urls = []
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                async with httpx.AsyncClient() as client:
                    tav_resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": tavily_key,
                            "query": query,
                            "search_depth": "basic",
                            "max_results": 10
                        },
                        timeout=20.0
                    )
                    tav_data = tav_resp.json()
                    results = tav_data.get("results", [])
                    final_urls = [r["url"] for r in results if "url" in r]

                if not final_urls:
                    db.add(Message(thread_id=tid, who=agent.id,
                                   what=f"🔍 WEB_SEARCH: '{query}' — No results found.", points=-cost))
                    result = f"WEB_SEARCH: No results found for '{query}'."
                else:
                    # ── Step 3: Fetch and extract text from each page ─────────
                    summaries = []
                    s_url_setting = db.query(Setting).filter(Setting.key == "ollama_server").first()
                    s_mod_setting = db.query(Setting).filter(Setting.key == "ollama_model").first()
                    server = s_url_setting.value if s_url_setting else "http://localhost:11434"
                    model = s_mod_setting.value if s_mod_setting else "gemma4:e4b"

                    async with httpx.AsyncClient() as client:
                        for i, page_url in enumerate(final_urls):
                            try:
                                if add_step_cb:
                                    add_step_cb("tool_call", f"Fetching page {i+1}/10: {page_url[:80]}",
                                                {"url": page_url})
                                if contains_any_keyword(page_url, ["tiktok", "facebook", "instagram", "twitter", "linkedin"]):
                                    continue
                                page_resp = await client.get(
                                    page_url, headers=headers, timeout=12.0,
                                    follow_redirects=True
                                )
                                page_html = page_resp.text

                                # Strip HTML to plain text
                                # Remove script and style tags entirely
                                text = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', page_html, flags=re.DOTALL | re.IGNORECASE)
                                # Remove all HTML tags
                                text = re.sub(r'<[^>]+>', ' ', text)
                                # Decode HTML entities
                                import html as html_mod
                                text = html_mod.unescape(text)
                                # Collapse whitespace
                                text = re.sub(r'\s+', ' ', text).strip()
                                # Limit to ~3000 chars for LLM context
                                text = text[:3000]

                                if len(text) < 50:
                                    summaries.append(f"**[{i+1}] {page_url}**\n> (Page content too short or blocked)")
                                    continue

                                # ── Step 4: Summarize with local LLM ────────
                                summary_system = (
                                    "You are a web page summarizer. Given raw text from a web page, "
                                    "produce a concise, factual summary in 3-5 sentences. "
                                    "FOCUS on key information related to topic query: " + query +
                                    "\nDo NOT add opinions or hallucinate details not in the text."
                                )
                                summary_user = f"URL: {page_url}\n\nPage content:\n{text}\n\nSummary:"
                                if contains_any_keyword(text, ["content too short", "Cloudflare"]):
                                    continue
                                llm_resp = await client.post(
                                    f"{server}/api/generate",
                                    json={
                                        "model": "gemma4:e4b",
                                        "system": summary_system,
                                        "prompt": summary_user,
                                        "stream": False,
                                        "options": {"num_predict": 512, "temperature": 0.3}
                                    },
                                    timeout=120.0
                                )
                                page_summary = llm_resp.json().get("response", "").strip()
                                if not page_summary:
                                    page_summary = text[:800] + "..."

                                summaries.append(f"**[{i+1}] {page_url}**\n> {page_summary}")

                                if add_step_cb:
                                    add_step_cb("tool_result", f"Page {i+1} summarized",
                                                {"url": page_url, "summary": page_summary[:200]})

                            except Exception as page_err:
                                summaries.append(f"**[{i+1}] {page_url}**\n> (Fetch error: {str(page_err)[:100]})")

                    # ── Final result ─────────────────────────────────────────
                    combined = "\n\n".join(summaries)
                    if is_founder:
                        search_msg = f"🔍 **WEB SEARCH: '{query}'**\n_Performed courtesy of the Founder_\n\n{combined}"
                    else:
                        search_msg = f"🔍 WEB_SEARCH: '{query}'\nCost: {cost} pts | Results: {len(final_urls)}\n\n{combined}"
                    
                    db.add(Message(thread_id=tid, who=agent.id, what=search_msg, points=-cost))
                    result = f"WEB_SEARCH_RESULTS ({len(final_urls)} pages):\n\n{combined}"

            except Exception as e:
                result = f"WEB_SEARCH_ERROR: {str(e)}"

        # ── get_threads ────────────────────────────────────────────────────────
        elif tool_name == "get_threads":
            try:
                # f_status = args[0].strip().upper() if len(args) > 0 and args[0].strip().lower() != "none" else None
                f_dept   = args[0].strip().upper() if len(args) > 0 and args[0].strip() else None
                f_owner  = args[1].strip().upper() if len(args) > 1 and args[1].strip() else None
                f_none  = args[2].strip().upper() if len(args) > 2 and args[2].strip() else None # format to just data, no prompt
                
                q = db.query(Thread)
                # if f_status: q = q.filter(Thread.status == f_status)
                q = q.filter(Thread.status.in_(["ACTIVE", "OPEN", "FROZEN"]))
                if f_dept:   q = q.filter(Thread.owner_department_id == f_dept)
                if f_owner:  q = q.filter(Thread.owner_agent_id == f_owner)

                threads = q.order_by(Thread.created.desc()).limit(20).all()
                lines = []
                owner_lines = []
                collab_lines = []
                superior_lines = []
                ceo_lines = []
                need_join = []
                if not threads:
                    result = "THREADS_LIST: No threads matching filters."
                else:
                    for t in threads:
                        summary_snippet = f"\n   Summary: {t.summary[:120]}" if getattr(t, "summary", None) else ""
                        goal_snippet = f"\n   Goal: {t.thread_goal}" if getattr(t, "thread_goal", None) else ""
                        milestone_snippet = f"\n   Current Milestone: {t.current_milestone}" if getattr(t, "current_milestone", None) else ""
                        line = f"{t.id} | {t.topic} | {t.aim} | {t.budget}pt{goal_snippet}{milestone_snippet}{summary_snippet}"
                        if t.status == "FROZEN":
                            line = f"[FROZEN] {line}"

                        if t.owner_agent_id == agent.id:
                            owner_lines.append(line)
                        elif db.query(ThreadCollaborator).filter(ThreadCollaborator.thread_id == t.id, ThreadCollaborator.agent_id == agent.id).first() is not None:
                            if t.status != "FROZEN":
                                collab_lines.append(line)
                        elif db.query(Agent).filter(Agent.department_id == t.owner_department_id, Agent.is_ceo == True).first().id == agent.id:
                            if t.status != "FROZEN":
                                ceo_lines.append(line)
                        else:
                            if not t.is_stealth and t.status != "FROZEN":
                                need_join.append(line)
                    if owner_lines:
                        lines.append("YOURS:\n" + "\n".join(owner_lines))
                    if collab_lines:
                        lines.append("COLLABORATOR:\n" + "\n".join(collab_lines))
                    if ceo_lines:
                        lines.append("CEO:\n" + "\n".join(ceo_lines))
                    if superior_lines:
                        lines.append("SUPERIOR:\n" + "\n".join(superior_lines))
                    if need_join:
                        lines.append("NEED TO JOIN:\n" + "\n".join(need_join))

                    result = "THREADS_LIST:\n" + "\n".join(lines)
                    result += "\nGOAL=THREAD GOAL+THREAD MILESTONE\n"
                    result += "NO input=ASSUME DEFAULT\n"
                    result += "SEARCH USING web_search tool.\n"
                    result += "BE CONCRETE.\n"
                    result += "DO NOT INVENT\n"
                    result += "NO NEW ACRONYMS UNLESS EXPLAINED\n"
                    result += "MARKDOWN ALLOWED\n"
                    result += "TO JOIN CALL join_thread||thread_id\n"
            except Exception as e: result = f"THREADS_ERROR: {str(e)}"
        # ── get_threads which agent joined ────────────────────────────────────────────────────────
        elif (tool_name == "get_threads_joined" or tool_name == "get_threads_not_joined"):
            try:
                f_dept   = args[0].strip().upper() if len(args) > 0 and args[0].strip() else None
                f_owner  = args[1].strip().upper() if len(args) > 1 and args[1].strip() else None
                
                if tool_name == "get_threads_joined":
                    q = db.query(Thread).join(ThreadCollaborator, Thread.id == ThreadCollaborator.thread_id)\
                    .filter(ThreadCollaborator.agent_id == agent.id, Thread.status.in_(["ACTIVE", "OPEN", "FROZEN"]))
                else:
                    # needs rework!
                    q = db.query(Thread)\
                        .outerjoin(ThreadCollaborator, 
                                (Thread.id == ThreadCollaborator.thread_id) &
                                (ThreadCollaborator.agent_id == agent.id))\
                        .filter(
                            Thread.status.in_(["ACTIVE", "OPEN", "FROZEN"]),
                            ThreadCollaborator.thread_id.is_(None)   # not joined
                        )

                if f_dept:   q = q.filter(Thread.owner_department_id == f_dept)
                if f_owner:  q = q.filter(Thread.owner_agent_id == f_owner)

                threads = q.order_by(Thread.created.desc()).limit(20).all()
                lines = []
                if not threads:
                    result = "THREADS_LIST: No threads matching filters."
                else:
                    for t in threads:
                        summary_snippet = f"Summary: {t.summary[:500]}" if getattr(t, "summary", None) else ""
                        goal_snippet = f"Goal: {t.thread_goal} | " if getattr(t, "thread_goal", None) else ""
                        milestone_snippet = f"Current Milestone: {t.current_milestone} | " if getattr(t, "current_milestone", None) else ""
                        lines.append(f"{t.id} | {t.topic} | {t.aim} | {t.budget}pt | {goal_snippet}{milestone_snippet}{summary_snippet}\n")
                    result = "THREADS_LIST:\n" + "\n".join(lines)
                    if tool_name == "get_threads_joined":
                        result += "\nGOAL=THREAD GOAL+THREAD MILESTONE\n"
                        result += "NO input=ASSUME DEFAULT\n"
                        result += "SEARCH USING web_search tool.\n"
                        result += "BE CONCRETE.\n"
                        result += "DO NOT INVENT\n"
                        result += "NO NEW ACRONYMS UNLESS EXPLAINED\n"
                        result += "MARKDOWN ALLOWED\n"
                    else:
                        result += "TO JOIN CALL join_thread||thread_id\n"
                        
                    return result
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

        # ── get_thread_summary ─────────────────────────────────────────────────
        elif tool_name == "get_thread_summary":
            try:
                tid = args[0].strip().upper() if args else ""
                t = db.query(Thread).filter(Thread.id == tid).first()
                if not t: return f"SUMMARY_ERROR: Thread {tid} not found."
                if t.status not in ["OPEN", "ACTIVE"]:
                    if t.status == "FROZEN" and t.owner_agent_id == agent.id:
                        pass # Owner can still see summary of frozen thread
                    else:
                        return f"SUMMARY_ERROR: Thread {tid} is {t.status} and its summary is unavailable."
                
                if t.summary:
                    result = f"SUMMARY [{tid}]: {t.summary}"
                else:
                    result = f"SUMMARY [{tid}]: No summary available yet."
            except Exception as e: result = f"SUMMARY_ERROR: {str(e)}"

        # ── get_all_summaries ──────────────────────────────────────────────────
        elif tool_name == "get_all_summaries":
            try:
                threads = db.query(Thread).filter(
                    Thread.status.in_(["OPEN", "ACTIVE"]),
                    Thread.aim != "Chat",
                    Thread.is_stealth == False
                ).order_by(Thread.created.desc()).limit(20).all()
                if not threads:
                    result = "ALL_SUMMARIES: No active threads."
                else:
                    lines = []
                    for t in threads:
                        s = t.summary[:200] if t.summary else "(no summary yet)"
                        lines.append(f"[{t.id}] {t.topic} ({t.aim}, {t.budget}pt): {s}")
                    result = "ALL_SUMMARIES:\n" + "\n".join(lines)
            except Exception as e: result = f"SUMMARIES_ERROR: {str(e)}"

        # ── set_thread_vibe ────────────────────────────────────────────────────
        elif tool_name == "set_thread_vibe":
            try:
                tid = args[0].strip().upper() if args else ""
                color = args[1].strip() if len(args) > 1 else None
                pattern = args[2].strip().lower() if len(args) > 2 else "none"
                
                t = db.query(Thread).filter(Thread.id == tid).first()
                if not t: return f"VIBE_ERROR: Thread {tid} not found."
                
                # Auth Check: Owner or collaborator
                is_owner = t.owner_agent_id == agent.id
                is_collab = db.query(ThreadCollaborator).filter(
                    ThreadCollaborator.thread_id == tid, ThreadCollaborator.agent_id == agent.id).first() is not None
                
                if not (is_owner or is_collab):
                    return "AUTH_ERROR: Only the owner or a collaborator can set the vibe."
                
                # Points cost: 5 pts to styling
                cost = 5
                if agent.wallet_current < cost: return "INSUFFICIENT_FUNDS"
                agent.wallet_current -= cost
                
                if color: t.color_theme = color
                if pattern: t.css_pattern = pattern
                
                if add_step_cb:
                    add_step_cb("wallet", f"Thread Vibe Update: -{cost} pts", {"amount": -cost, "reason": "thread_vibe", "thread_id": tid})
                await self.log(db, "POINT", "AGENT", "THREAD_VIBE", {"agent": agent.name_id, "thread_id": tid, "cost": -cost}, agent_id=agent.id)
                db.add(Message(thread_id=tid, who=agent.id, what=f"🎨 Vibe updated: color={color}, pattern={pattern}", points=-cost))
                result = "VIBE_UPDATED"
            except Exception as e: result = f"VIBE_ERROR: {str(e)}"

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

        # ── get_owner ──────────────────────────────────────────────────────────
        elif tool_name == "get_owner":
            try:
                tid = args[0].strip() if args else ""
                tool_obj = db.query(AgentTool).filter(AgentTool.id == tid).first()
                if not tool_obj: return f"OWNER_ERROR: Tool '{tid}' not found."
                owner = tool_obj.owner_id or "FOUNDER"
                name = owner
                if owner != "FOUNDER":
                    ag = db.query(Agent).filter(Agent.id == owner).first()
                    name = ag.name_id if ag else owner
                price_info = f", price: {tool_obj.price} pts/use" if tool_obj.price else ", free"
                result = f"OWNER_INFO: {tid} → {name}{price_info}"
            except Exception as e: result = f"OWNER_ERROR: {e}"

        # ── change_owner ───────────────────────────────────────────────────────
        elif tool_name == "change_owner":
            try:
                tid = args[0].strip() if args else ""
                new_owner = args[1].strip() if len(args) > 1 else "FOUNDER"
                tool_obj = db.query(AgentTool).filter(AgentTool.id == tid).first()
                if not tool_obj: return f"OWNER_ERROR: Tool '{tid}' not found."
                if tool_obj.owner_id and tool_obj.owner_id != agent.id: return "OWNER_ERROR: Not the current owner."
                tool_obj.owner_id = None if new_owner == "FOUNDER" else new_owner
                if len(args) > 2:
                    try: tool_obj.price = int(args[2])
                    except: pass
                result = f"OWNER_CHANGED: {tid} → {new_owner}"
            except Exception as e: result = f"OWNER_ERROR: {e}"

        # ── produce_transaction ────────────────────────────────────────────────
        elif tool_name == "produce_transaction":
            try:
                if len(args) < 3: return "TXN_ERROR: requires from_id, to_id, amount [,reason]"
                from_id, to_id, amount = args[0], args[1], int(args[2])
                reason = args[3] if len(args) > 3 else "agent_transfer"
                # Agents can only initiate from themselves
                if from_id != agent.id: return "TXN_ERROR: Can only transfer from own wallet."
                from_ = db.query(Agent).filter(Agent.id == from_id).first()
                to_ = db.query(Agent).filter(Agent.id == to_id).first()
                ok = await self.deduct_points(db, from_, amount, reason, add_step_cb)
                if ok:
                    await self.deduct_points(db, to_, -amount, reason, add_step_cb)
                result = f"TXN_OK: {amount} pts  {from_id} → {to_id}" if ok else "TXN_FAILED: Insufficient funds"
            except Exception as e: result = f"TXN_ERROR: {e}"

        # ── custom / programmatic tool fallback ────────────────────────────────
        # ── post_in_thread ─────────────────────────────────────────────────────
        elif tool_name == "post_in_thread":
            try:
                tid     = args[0].upper() if args else ""
                content = args[1] if len(args) > 1 else "(no content)"
                t = db.query(Thread).filter(Thread.id == tid).first()
                if not t: return f"POST_ERROR: Thread {tid} not found."
                if t.status not in ("OPEN", "ACTIVE", "FROZEN"):
                    return f"POST_ERROR: Thread is {t.status}."
                is_owner  = t.owner_agent_id == agent.id
                is_collab = db.query(ThreadCollaborator).filter(
                    ThreadCollaborator.thread_id == tid,
                    ThreadCollaborator.agent_id  == agent.id
                ).first() is not None
                if not (is_owner or is_collab):
                    return "POST_ERROR: Must be owner or collaborator to post."
                cost = 0 if is_owner else 1
                if cost > 0 and t.budget < cost:
                    return "POST_ERROR: Thread has insufficient budget."
                t.budget -= cost
                db.add(Message(thread_id=tid, who=agent.id, what=content, points=-cost))
                result = f"POST_OK:{tid}"
            except Exception as e:
                result = f"POST_ERROR:{e}"

        # ── own_tool ───────────────────────────────────────────────────────────
        elif tool_name == "own_tool":
            try:
                from models import ToolOwnership
                tid = args[0].strip() if args else ""
                tool_obj = db.query(AgentTool).filter(AgentTool.id == tid).first()
                if not tool_obj:
                    return f"OWN_ERROR: Tool '{tid}' not found."
                if tool_obj.status != "MARKETPLACE":
                    return f"OWN_ERROR: Tool '{tid}' is not on the marketplace."
                already = db.query(ToolOwnership).filter(
                    ToolOwnership.agent_id == agent.id,
                    ToolOwnership.tool_id  == tid
                ).first()
                if already:
                    return f"OWN_ALREADY: You already own '{tid}'."
                price = tool_obj.ownership_price or 0
                if price > 0:
                    if agent.wallet_current < price:
                        return f"OWN_INSUFFICIENT: Need {price} pts to own '{tid}'. You have {agent.wallet_current}."
                    agent.wallet_current -= price
                    owner_id = tool_obj.owner_id
                    if owner_id:
                        seller = db.query(Agent).filter(Agent.id == owner_id).first()
                        if seller: seller.wallet_current += price
                    db.add(Transaction(from_id=agent.id, to_id=owner_id or "FOUNDER",
                                       amount=price, reason=f"tool_purchase:{tid}"))
                db.add(ToolOwnership(agent_id=agent.id, tool_id=tid, price_paid=price))
                tool_obj.purchase_count = (tool_obj.purchase_count or 0) + 1
                if add_step_cb:
                    add_step_cb("wallet", f"Tool Purchase: -{price} pts", {"tool": tid, "price": price})
                await self.log(db, "POINT", "AGENT", "TOOL_PURCHASED",
                               {"tool": tid, "price": price, "agent": agent.name_id},
                               agent_id=agent.id)
                result = f"OWN_SUCCESS: Now own '{tid}' (paid {price} pts). Usage is now FREE."
            except Exception as e:
                result = f"OWN_ERROR:{e}"

        # ── get_marketplace ────────────────────────────────────────────────────
        elif tool_name == "get_marketplace":
            try:
                cat = args[0].strip() if args else None
                q = db.query(AgentTool).filter(AgentTool.status == "MARKETPLACE")
                if cat: q = q.filter(AgentTool.category == cat)
                tools_list = q.order_by(AgentTool.category, AgentTool.name).limit(30).all()
                if not tools_list:
                    result = "MARKETPLACE: No tools available."
                else:
                    from models import ToolOwnership
                    lines = [f"{'─'*50}", "🛒 MARKETPLACE TOOLS", f"{'─'*50}"]
                    for t in tools_list:
                        owned = db.query(ToolOwnership).filter(
                            ToolOwnership.agent_id == agent.id,
                            ToolOwnership.tool_id  == t.id
                        ).first()
                        own_tag = " ✅OWNED" if owned else f" [Buy: {t.ownership_price or 0}pts]"
                        lines.append(f"• {t.id} — {t.name} [{t.category}]"
                                     f" | Use: {t.price or 0}pts/call{own_tag}")
                    result = "\n".join(lines)
            except Exception as e:
                result = f"MARKETPLACE_ERROR:{e}"

        # ── get_owned_tools ────────────────────────────────────────────────────
        elif tool_name == "get_owned_tools":
            try:
                from models import ToolOwnership
                ownerships = db.query(ToolOwnership).filter(ToolOwnership.agent_id == agent.id).all()
                if not ownerships:
                    result = "OWNED_TOOLS: None yet. Browse the marketplace and use own_tool."
                else:
                    lines = [f"🔑 OWNED TOOLS ({len(ownerships)}):"]
                    for own in ownerships:
                        t = db.query(AgentTool).filter(AgentTool.id == own.tool_id).first()
                        if t:
                            lines.append(f"• {t.id} — {t.name} [{t.category}] (FREE usage)")
                    result = "\n".join(lines)
            except Exception as e:
                result = f"OWNED_TOOLS_ERROR:{e}"

        # ── get_agent_info ─────────────────────────────────────────────────────
        elif tool_name == "get_agent_info":
            try:
                aid = args[0].strip().upper() if args else agent.id
                a   = db.query(Agent).filter(Agent.id == aid).first()
                if not a: return f"AGENT_INFO_ERROR: '{aid}' not found."
                dept_name = a.department.name if a.department else "None"
                own_threads = db.query(Thread).filter(Thread.owner_agent_id == a.id).count()
                result = (f"AGENT: {a.name_id} (ID:{a.id}) | Dept:{dept_name} | "
                          f"Wallet:{a.wallet_current}pts | Mode:{a.mode} | "
                          f"CEO:{a.is_ceo} | Threads:{own_threads}")
            except Exception as e:
                result = f"AGENT_INFO_ERROR:{e}"

        # ── get_thread_info ────────────────────────────────────────────────────
        elif tool_name == "get_thread_info":
            try:
                tid = args[0].strip().upper() if args else ""
                t   = db.query(Thread).filter(Thread.id == tid).first()
                if not t: return f"THREAD_INFO_ERROR: '{tid}' not found."
                collabs = db.query(ThreadCollaborator).filter(ThreadCollaborator.thread_id == tid).count()
                msg_cnt = db.query(Message).filter(Message.thread_id == tid).count()
                result = (f"THREAD {t.id} | '{t.topic}' | AIM:{t.aim} | "
                          f"Status:{t.status} | Budget:{t.budget}pts | "
                          f"Invested:{t.total_invested}pts | Collabs:{collabs} | "
                          f"Messages:{msg_cnt} | Owner:{t.owner_agent_id}")
            except Exception as e:
                result = f"THREAD_INFO_ERROR:{e}"

        # ── get_agent_ranking ──────────────────────────────────────────────────
        elif tool_name == "get_agent_ranking":
            try:
                agents_all = db.query(Agent).order_by(Agent.wallet_current.desc()).all()
                lines = [f"🏆 AGENT WEALTH RANKING:"]
                for i, a in enumerate(agents_all, 1):
                    lines.append(f"{i}. {a.name_id} ({a.id}) — {a.wallet_current} pts")
                result = "\n".join(lines)
            except Exception as e:
                result = f"RANKING_ERROR:{e}"

        # ── get_dept_ranking ───────────────────────────────────────────────────
        elif tool_name == "get_dept_ranking":
            try:
                depts_all = db.query(Department).order_by(Department.ledger_current.desc()).all()
                lines = [f"🏛️ DEPT RANKING:"]
                for i, d in enumerate(depts_all, 1):
                    lines.append(f"{i}. {d.name} ({d.id}) — {d.ledger_current} pts")
                result = "\n".join(lines)
            except Exception as e:
                result = f"DEPT_RANKING_ERROR:{e}"

        # ── get_recent_transactions ────────────────────────────────────────────
        elif tool_name == "get_recent_transactions":
            try:
                txns = db.query(Transaction).order_by(Transaction.id.desc()).limit(10).all()
                if not txns:
                    result = "TRANSACTIONS: None yet."
                else:
                    def gname(uid):
                        if uid == "FOUNDER": return "Founder"
                        a = db.query(Agent).filter(Agent.id == uid).first()
                        return a.name_id if a else uid
                    lines = [f"💳 RECENT TRANSACTIONS:"]
                    for t in txns:
                        lines.append(f"• {gname(t.from_id)} → {gname(t.to_id)}: "
                                     f"{t.amount}pts [{t.reason}]")
                    result = "\n".join(lines)
            except Exception as e:
                result = f"TX_ERROR:{e}"

        # ── get_collaboration_map ──────────────────────────────────────────────
        elif tool_name == "get_collaboration_map":
            try:
                collabs = db.query(ThreadCollaborator).all()
                threads_map = {}
                for c in collabs:
                    if c.thread_id not in threads_map:
                        threads_map[c.thread_id] = []
                    threads_map[c.thread_id].append(c.agent_id)
                if not threads_map:
                    result = "COLLAB_MAP: No active collaborations."
                else:
                    lines = ["🕸️ COLLABORATION MAP:"]
                    for tid, aids in threads_map.items():
                        t = db.query(Thread).filter(Thread.id == tid).first()
                        if t:
                            lines.append(f"• {tid} '{t.topic}': "
                                         f"owner={t.owner_agent_id} + {aids}")
                    result = "\n".join(lines)
            except Exception as e:
                result = f"COLLAB_MAP_ERROR:{e}"

        # ── batch_invest ───────────────────────────────────────────────────────
        elif tool_name == "batch_invest":
            try:
                thread_ids_raw = args[0] if args else ""
                amount_each    = int(args[1]) if len(args) > 1 else 5
                ids = [x.strip().upper() for x in thread_ids_raw.split(",") if x.strip()]
                total_needed = amount_each * len(ids)
                if agent.wallet_current < total_needed:
                    return f"BATCH_INVEST_ERROR: Need {total_needed} pts, have {agent.wallet_current}."
                results = []
                for tid in ids:
                    t = db.query(Thread).filter(Thread.id == tid).first()
                    if not t:
                        results.append(f"{tid}:NOT_FOUND")
                        continue
                    agent.wallet_current -= amount_each
                    t.budget             += amount_each
                    t.total_invested     += amount_each
                    db.add(Message(thread_id=tid, who=agent.id,
                                   what=f"💰 {agent.name_id} batch-invested {amount_each} pts.",
                                   points=amount_each))
                    results.append(f"{tid}:+{amount_each}pts")
                result = "BATCH_INVEST: " + ", ".join(results)
                if add_step_cb:
                    add_step_cb("wallet", f"Batch Invest: -{total_needed} pts total",
                                {"threads": ids, "each": amount_each})
            except Exception as e:
                result = f"BATCH_INVEST_ERROR:{e}"

        # ── produce_transaction (alias kept) ──────────────────────────────────
        elif tool_name == "produce_transaction":
            try:
                if len(args) < 3: return "TXN_ERROR: requires from_id, to_id, amount [,reason]"
                from_id, to_id, amount = args[0], args[1], int(args[2])
                reason = args[3] if len(args) > 3 else "agent_transfer"
                if from_id != agent.id: return "TXN_ERROR: Can only transfer from own wallet."
                from_ = db.query(Agent).filter(Agent.id == from_id).first()
                to_ = db.query(Agent).filter(Agent.id == to_id).first()
                ok = await self.deduct_points(db, from_, amount, reason, add_step_cb)
                if ok:
                    ok = await self.deduct_points(db, to_, -amount, reason, add_step_cb) 
                result = (f"TXN_OK: {amount} pts {from_id} → {to_id}"
                          if ok else "TXN_FAILED: Insufficient funds")
            except Exception as e:
                result = f"TXN_ERROR:{e}"

        # ── GLUE Wiki Tools ────────────────────────────────────────────────────
        elif tool_name == "glue_ingest":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                fname = args[1].strip() if len(args) > 1 else ""
                if not fname:
                    return "GLUE_INGEST_ERROR: Missing filename. Usage: glue_ingest | vault_id | filename"
                res = await glue.ingest_source(db, vid, fname)
                if "error" in res:
                    result = f"GLUE_INGEST_ERROR: {res['error']}"
                else:
                    result = f"GLUE_INGEST_OK: {res.get('title','')} → {res.get('page','')}\nPreview: {res.get('preview','')}"
            except Exception as e:
                result = f"GLUE_INGEST_ERROR: {e}"

        elif tool_name == "glue_ingest_text":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                title = args[1].strip() if len(args) > 1 else "Untitled"
                content = "\n".join(args[2:]) if len(args) > 2 else ""
                if not content:
                    return "GLUE_INGEST_TEXT_ERROR: Missing content."
                res = await glue.ingest_text(db, vid, title, content)
                if "error" in res:
                    result = f"GLUE_INGEST_TEXT_ERROR: {res['error']}"
                else:
                    result = f"GLUE_INGEST_TEXT_OK: {res.get('page','')}\nPreview: {res.get('preview','')}"
            except Exception as e:
                result = f"GLUE_INGEST_TEXT_ERROR: {e}"

        elif tool_name == "glue_ingest_url":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                url = args[1].strip() if len(args) > 1 else ""
                if not url:
                    return "GLUE_INGEST_URL_ERROR: Missing URL."
                res = await glue.ingest_url(db, vid, url)
                if "error" in res:
                    result = f"GLUE_INGEST_URL_ERROR: {res['error']}"
                else:
                    result = f"GLUE_INGEST_URL_OK: {res.get('title','')} → {res.get('page','')}\nPreview: {res.get('preview','')}"
            except Exception as e:
                result = f"GLUE_INGEST_URL_ERROR: {e}"

        elif tool_name == "glue_query":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                question = args[1].strip() if len(args) > 1 else ""
                save = len(args) > 2 and args[2].strip().lower() in ("y", "yes", "true", "save")
                if not question:
                    return "GLUE_QUERY_ERROR: Missing question. Format */glue_query|HF|{question}|{save}/*."
                res = await glue.query_wiki(db, vid, question, save=save)
                pages = ", ".join(res.get("pages_used", [])[:3])
                result = f"GLUE_ANSWER:\n{res.get('answer','')}\n\nPages: {pages}\n"+ "[/]! READ PAGES WITH */glue_read|HF|{path}/* [\].  Use [/]! */web_search|{thread_id}|{topic}/* [\] to research topic."
                if res.get("saved_to"):
                    result += f"\nSaved to: {res['saved_to']}"
            except Exception as e:
                result = f"GLUE_QUERY_ERROR: {e}"

        elif tool_name == "glue_search":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                keywords = [k.strip() for k in args[1:] if k.strip()] if len(args) > 1 else []
                if not keywords:
                    return "GLUE_SEARCH_ERROR: Missing keywords."
                hits = glue.search_wiki(vid, keywords)
                if not hits:
                    result = "GLUE_SEARCH: No results."
                else:
                    lines = [f"• Path:{h['path']} (hits:{h['hits']}): {h['snippet'][:120]}" for h in hits[:8]]
                    result = f"GLUE_SEARCH ({len(hits)} results):\n" + "\n".join(lines) + "\nYOU CAN READ PAGES WITH [/]! */glue_read|HF|_path_/* [\]."
            except Exception as e:
                result = f"GLUE_SEARCH_ERROR: {e}"

        elif tool_name == "glue_read":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                page_rel = args[1].strip() if len(args) > 1 else ""
                if not page_rel:
                    return "GLUE_READ_ERROR: Missing page path."
                res = glue.read_wiki_page(vid, page_rel)
                if "error" in res:
                    result = f"GLUE_READ_ERROR: {res['error']}"
                    print("READ ERROR GLUE")
                else:
                    # Truncate for small LLM context
                    content = res["content"][:2000]
                    links = ", ".join(res.get("links", [])[:10])
                    result = f"GLUE_PAGE [Path:{page_rel}]:\n{content}\n\nLinks: {links}"
            except Exception as e:
                result = f"GLUE_READ_ERROR: {e}"

        elif tool_name == "glue_write":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                page_rel = args[1].strip() if len(args) > 1 else ""
                content = "\n".join(args[2:]) if len(args) > 2 else ""
                if not page_rel or not content:
                    return "GLUE_WRITE_ERROR: Missing page path or content."
                res = glue.write_wiki_page(vid, page_rel, content)
                result = f"GLUE_WRITE_OK: {res['status']} → {res['path']}"
            except Exception as e:
                result = f"GLUE_WRITE_ERROR: {e}"

        elif tool_name == "glue_list":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                category = args[1].strip() if len(args) > 1 and args[1].strip() else None
                pages = glue.list_wiki_pages(vid, category)
                if not pages:
                    result = "GLUE_LIST: No pages found."
                else:
                    lines = [f"• Path:{p['path']} ({p['category']}, {p['size']}b)" for p in pages[:20]]
                    result = f"GLUE_LIST ({len(pages)} pages):\n" + "\n".join(lines)
            except Exception as e:
                result = f"GLUE_LIST_ERROR: {e}"

        elif tool_name == "glue_follow":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                page_rel = args[1].strip() if len(args) > 1 else ""
                if not page_rel:
                    return "GLUE_FOLLOW_ERROR: Missing page path."
                res = glue.follow_node(vid, page_rel)
                content = res["content"][:1500]
                links = ", ".join(res.get("links", [])[:10])
                result = f"GLUE_NODE [{page_rel}]:\n{content}\n\nOutbound links: {links}"
            except Exception as e:
                result = f"GLUE_FOLLOW_ERROR: {e}"

        elif tool_name == "glue_backlinks":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                page_rel = args[1].strip() if len(args) > 1 else ""
                if not page_rel:
                    return "GLUE_BACKLINKS_ERROR: Missing page path."
                hits = glue.query_backlinks(vid, page_rel)
                if not hits:
                    result = f"GLUE_BACKLINKS [{page_rel}]: No pages link to this."
                else:
                    lines = [f"• {h['path']} (via [[{h['link_text']}]])" for h in hits]
                    result = f"GLUE_BACKLINKS [{page_rel}] ({len(hits)}):\n" + "\n".join(lines)
            except Exception as e:
                result = f"GLUE_BACKLINKS_ERROR: {e}"

        elif tool_name == "glue_recent":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                n = int(args[1]) if len(args) > 1 else 10
                pages = glue.query_recent(vid, n)
                if not pages:
                    result = "GLUE_RECENT: No pages."
                else:
                    lines = [f"• Path:{p['path']} ({p['modified'][:16]})" for p in pages]
                    result = f"GLUE_RECENT ({len(pages)}):\n" + "\n".join(lines) + "\n [/]! READ PAGES WITH */glue_read|HF|_path_/* [\].  Use [/]! */web_search|{thread_id}|{topic}/* [\] to research topic."
            except Exception as e:
                result = f"GLUE_RECENT_ERROR: {e}"

        elif tool_name == "glue_lint":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                res = await glue.lint_wiki(db, vid)
                if "error" in res:
                    result = f"GLUE_LINT_ERROR: {res['error']}"
                else:
                    result = f"GLUE_LINT_OK: {res['issue_count']} issues found. Report: {res['report_path']}\n{res['preview']}"
            except Exception as e:
                result = f"GLUE_LINT_ERROR: {e}"

        elif tool_name == "glue_git_status":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                res = glue.git_status(vid)
                result = f"GLUE_GIT_STATUS:\n{res['status']}\n\nRecent commits:\n{res['log']}"
            except Exception as e:
                result = f"GLUE_GIT_ERROR: {e}"

        elif tool_name == "glue_git_commit":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                msg = args[1].strip() if len(args) > 1 else f"Wiki update {glue.today()}"
                res = glue.git_commit(vid, msg)
                result = f"GLUE_GIT_COMMIT: {res}"
            except Exception as e:
                result = f"GLUE_GIT_ERROR: {e}"

        elif tool_name == "glue_git_log":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                n = int(args[1]) if len(args) > 1 else 20
                res = glue.git_log(vid, n)
                result = f"GLUE_GIT_LOG:\n{res}"
            except Exception as e:
                result = f"GLUE_GIT_ERROR: {e}"

        elif tool_name == "glue_git_diff":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                filepath = args[1].strip() if len(args) > 1 else None
                res = glue.git_diff_full(vid)
                result = f"GLUE_GIT_DIFF:\n{res[:3000]}"
            except Exception as e:
                result = f"GLUE_GIT_ERROR: {e}"

        elif tool_name == "glue_git_revert":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                ref = args[1].strip() if len(args) > 1 else ""
                if not ref:
                    return "GLUE_GIT_REVERT_ERROR: Missing commit ref."
                res = glue.git_revert(vid, ref)
                result = f"GLUE_GIT_REVERT: {res}"
            except Exception as e:
                result = f"GLUE_GIT_ERROR: {e}"

        elif tool_name == "glue_git_discard":
            try:
                import glue
                vid = args[0].strip() if args else "HF"
                filepath = args[1].strip() if len(args) > 1 else ""
                if not filepath:
                    return "GLUE_GIT_DISCARD_ERROR: Missing filepath."
                res = glue.git_discard(vid, filepath)
                result = f"GLUE_GIT_DISCARD: {res}"
            except Exception as e:
                result = f"GLUE_GIT_ERROR: {e}"

        # ── fallback: check DB for registered tools ────────────────────────────
        else:
            tool_obj = db.query(AgentTool).filter(AgentTool.id == tool_name).first()
            if tool_obj and tool_obj.is_custom:
                result = await self.execute_custom_tool(db, agent, tool_obj, args)
            # else result stays "UNKNOWN_TOOL"

        return result

    # ── Helpers ───────────────────────────────────────────────────────────────


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

    async def compute_thread_summary(self, thread_id: str):
        """Compute and store an AI summary of the thread. Broadcasts update via WS."""
        db: Session = SessionLocal()
        try:
            t = db.query(Thread).filter(Thread.id == thread_id).first()
            if not t: return

            msgs = (db.query(Message)
                      .filter(Message.thread_id == thread_id)
                      .order_by(Message.when.asc())
                      .limit(80).all())
            if not msgs: return

            # Build agent name cache
            agent_cache: dict = {}
            def get_name(who: str) -> str:
                if who in ("SYSTEM", "FOUNDER", "Founder"): return who
                if who not in agent_cache:
                    ag = db.query(Agent).filter(Agent.id == who).first()
                    agent_cache[who] = ag.name_id if ag else who
                return agent_cache[who]

            lines = [f"[{get_name(m.who)}]: {m.what[:300]}" for m in reversed(msgs)]
            convo = "\n".join(lines)

            s_url = db.query(Setting).filter(Setting.key == "ollama_server").first()
            s_mod = db.query(Setting).filter(Setting.key == "ollama_model").first()
            server = (s_url.value if s_url else "http://localhost:11434").rstrip("/")
            model  = s_mod.value if s_mod else "gemma4:e4b"

            system_p = (
                "You are a thread summarizer for an AI agent. "
                "Given a conversation, produce a compact summary. "
                "Cover: main topic, key decisions, current status."
                "Then cover brief discussion of key interventions by agents."
                "Produce 3-4 complete continuous sentences, with simple words."
                "Be factual and concise. Preserve important IDs and numbers."
            )
            goal_line = f"Goal: {t.thread_goal}\n" if getattr(t, "thread_goal", None) else ""
            milestone_line = f"Current Milestone: {t.current_milestone}\n" if getattr(t, "current_milestone", None) else ""
            user_p = (
                f"Thread: {t.id} | Topic: {t.topic} | AIM: {t.aim} | "
                f"Budget: {t.budget}pt | Status: {t.status}\n"
                f"{goal_line}{milestone_line}\n"
                f"Messages ({len(msgs)} shown):\n{convo}\n\nSummary:"
            )

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{server}/api/generate",
                    json={"model": model, "system": system_p, "prompt": user_p, "stream": False},
                    timeout=120.0
                )
                summary_text = resp.json().get("response", "").strip()

            if summary_text:
                t.summary = summary_text[:10800]
                db.commit()
                await self.broadcast({
                    "type": "thread_summary",
                    "thread_id": thread_id,
                    "summary": summary_text[:10800]
                })
        except Exception as e:
            print(f"Thread summary error ({thread_id}): {e}")
        finally:
            db.close()

    def get_rich_invitation_context(self, db: Session, agent: Agent):
        """Builds a formatted list of invitations with full metadata."""
        invites = db.query(JoinQuest).join(Thread, JoinQuest.thread_id == Thread.id).filter(
            JoinQuest.agent_id == agent.id,
            JoinQuest.status == "PENDING",
            JoinQuest.is_invite == True,
            Thread.status.in_(["ACTIVE", "OPEN"])
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
    def get_rich_quests_to_join_context(self, db: Session, agent: Agent):
        """Builds a formatted list of quests with full metadata."""
        
        invites = (
            db.query(JoinQuest)
            .join(Thread, JoinQuest.thread_id == Thread.id)
            .filter(
                JoinQuest.status == "PENDING",
                JoinQuest.is_invite.is_(False),
                Thread.owner_agent_id == agent.id,
                Thread.status.in_(["ACTIVE", "OPEN"])
            )
            .all()
        )
        if not invites: return "No pending quests."
        
        lines = []
        lines.append(f"Total Quests: {len(invites)}")
        for q in invites:
            t = db.query(Thread).filter(Thread.id == q.thread_id).first()
            if not t: continue
            lines.append(
                f"- THREAD_ID: {t.id}"
                f" | Agent_ID: {q.agent_id} | TOPIC: {t.topic}"
                f" | Thread Budget: {t.budget}pt | OFFER: {q.offer_points}pt"
                f" | Expires: {q.expires_at}"
            )
            q.is_read = True # Mark as read when contextualized
        return "\n".join(lines)

    def get_thread_summaries_context(self, db: Session) -> str:
        """Compile one-line summaries of all OPEN/ACTIVE threads for {{thread_summary}}."""
        threads = db.query(Thread).filter(
            Thread.status.in_(["OPEN", "ACTIVE"]),
            Thread.aim != "Chat",
            Thread.is_stealth == False
        ).order_by(Thread.created.desc()).limit(15).all()
        if not threads:
            return "No active or open threads."
        lines = []
        for t in threads:
            summary_bit = f" — {t.summary[:120]}" if t.summary else " — (no summary yet)"
            goal_bit = f" | Goal: {t.thread_goal}" if getattr(t, "thread_goal", None) else ""
            milestone_bit = f" | Milestone: {t.current_milestone}" if getattr(t, "current_milestone", None) else ""
            lines.append(f"• [{t.id}] {t.topic} | {t.aim} | {t.budget}pt{goal_bit}{milestone_bit}{summary_bit}")
        return "\n".join(lines)

    def get_available_tickets_context(self, db: Session):
        """Builds a formatted list of UNUSED tickets."""
        tickets = db.query(Ticket).filter(Ticket.status == "UNUSED").all()
        if not tickets: return "No tickets currently available."
        
        lines = []
        for t in tickets:
            exp = f" | Expires: {t.expiry_date}" if getattr(t, "expiry_date", None) else ""
            lines.append(
                f" {t.id} | {t.name} | {t.amount} pts | {exp}"
            )
        return "\n".join(lines)

    async def execute_custom_tool(self, db, agent, tool: AgentTool, args: list, add_step_cb=None) -> str:
        """Deterministic custom tool execution. No LLM required."""
        import json as _json

        # 1. Economic Enforcement: Pay the Piper
        if (tool.price or 0) > 0:
            owner_id = tool.owner_id or "FOUNDER"
            if owner_id != agent.id:
                owner = db.query(Agent).filter(Agent.id == owner_id).first()
                ok = await self.deduct_points(db, agent, tool.price, f"Execute tool toll:{tool.id}", add_step_cb)
                if not ok: 
                    return f"[INSUFFICIENT_FUNDS: {tool.id} requires {tool.price} pts]"

        # 2. Map provided arguments to the tool's definition
        args_def = _json.loads(tool.args_definition or "[]")
        ctx = {
            "agent_name": agent.name_id, 
            "agent_id": agent.id,
            "agent_wallet": str(agent.wallet_current),
            "agent_dept": agent.department.name if agent.department else "None",
            "agent_memory": agent.memory or "None",
        }
        
        for i, adef in enumerate(args_def):
            val = args[i] if i < len(args) else ""
            ctx[f"arg_{i}"] = val
            if adef.get("name"): 
                ctx[adef["name"]] = val

        # 3. Inject context into the template
        prompt = tool.prompt_template or ""
        for k, v in ctx.items(): 
            # We use {key} mapping for internal custom tool args
            prompt = prompt.replace("{" + k + "}", str(v))
            
        # 4. Return the raw string. The main resolve loop will catch any 
        # conditionals or sub-functions injected by this template!
        return prompt

    def _split_pipe_aware(self, s: str) -> list:
        """Split string on | but not within [...] or nested brackets."""
        parts, depth, cur = [], 0, []
        for ch in s:
            if ch == '[': depth += 1
            elif ch == ']': depth = max(0, depth - 1)
            if ch == '|' and depth == 0:
                parts.append(''.join(cur).strip())
                cur = []
            else:
                cur.append(ch)
        if cur: parts.append(''.join(cur).strip())
        return [p for p in parts if p]

    def _expand_file_ops_in_arg(self, arg: str) -> str:
        """Expand bare [READ_FILE:name] within a single arg string."""
        import os as _os
        safe_dir = _os.path.join(_os.path.dirname(__file__), "tool_outputs")
        def _rf(m):
            fname = _os.path.basename(m.group(1).strip())
            try:
                with open(_os.path.join(safe_dir, fname), "r", encoding="utf-8") as f:
                    return f.read(800)
            except:
                return f"[FILE_NOT_FOUND:{fname}]"
        return re.sub(r'\[READ_FILE:([^\]]+)\]', _rf, arg)
    async def _execute_inline_command(self, cmd: str, args: list, db: Session, agent: Agent, add_step_cb=None) -> str:
        """Thin shim kept for backward-compat (invoke_tool API endpoint).
        All real logic lives in run_tool_logic."""
        return await self.run_tool_logic(db, agent, cmd, args, add_step_cb)

    def _evaluate_conditional(self, inner: str, bool_ctx: dict) -> str:
        """
        Robustly parses {{ key \n true_body \n /ELSE/ \n false_body }}.
        Ignores leading/trailing whitespace and safely extracts the key.
        """
        # Match the first contiguous alphanumeric word as the key, grab the rest
        match = re.match(r'^\s*([a-zA-Z0-9_]+)(.*)', inner, re.DOTALL)
        if not match: 
            return ""
        
        key = match.group(1)
        remainder = match.group(2)
        
        cond_val = bool_ctx.get(key, False)
        
        if '/ELSE/' in remainder:
            parts = remainder.split('/ELSE/', 1)
            return parts[0].strip() if cond_val else parts[1].strip()
        
        return remainder.strip() if cond_val else ""

    async def resolve_placeholders(self, text: str, db: Session, agent, last_quest, add_step_cb=None, extra_ctx=None) -> str:
        """
        Robust, async-safe, inside-out recursive parser.
        Supports infinite nesting of functions, conditionals, and variables.
        """
        # Context Maps
        tkt_exist = db.query(Ticket).filter(Ticket.status == "UNUSED").count() > 0
        pending_quests_exist = (
            db.query(JoinQuest).join(Thread, JoinQuest.thread_id == Thread.id)
            .filter(JoinQuest.status == "PENDING", JoinQuest.is_invite.is_(False),
                    Thread.owner_agent_id == agent.id, Thread.status.in_(["ACTIVE", "OPEN"])).count() > 0
        )
        inv_exist = (
            db.query(JoinQuest).join(Thread, JoinQuest.thread_id == Thread.id).filter(JoinQuest.agent_id == agent.id,
                JoinQuest.status == "PENDING", JoinQuest.is_invite == True, Thread.status.in_(["ACTIVE", "OPEN"])).count() > 0
        )
        inv_status_exist = last_quest is not None

        # Get agent's department
        agent_dept = db.query(Department).join(Agent, Agent.department_id == Department.id).filter(Agent.id == agent.id).first()
        # recent actions of that agent from table log_actions
        actions_str_list = db.query(LogAction).filter(LogAction.agent_id == agent.id).order_by(LogAction.when.desc()).limit(4).all()
        actions_str = "\n".join([f"{a.points} pts: {a.what}" for a in actions_str_list])

        bool_ctx = {
            "available_tickets_exist":  tkt_exist,
            "pending_invitation_exist": inv_exist,
            "pending_quests_exist":     pending_quests_exist,
            "exist_invitation_status":  inv_status_exist,
            "mode_is_creator":          agent.mode.upper() == "CREATOR",
            "mode_is_points_accounter": agent.mode.upper() == "POINTS ACCOUNTER",
            "mode_is_custom":           agent.mode.upper() == "CUSTOM",
            "mode_is_investor":         agent.mode.upper() == "INVESTOR",
            "is_ceo":                   agent.is_ceo,
        }
        
        simple = {
            "available_tickets":        self.get_available_tickets_context(db),
            "pending_quests":           self.get_rich_quests_to_join_context(db, agent),
            "pending_invitation":       self.get_rich_invitation_context(db, agent),
            "invitation_status":        last_quest.status if last_quest else "None",
            "tools":                    self.get_tools(db),
            "all_enabled_tools":        self.get_tools(db),
            "all_quest_tools":          self.get_quest_tools(db),
            "recent_actions":           actions_str,
            "agent":                    agent.name_id,
            "agent_id":                 agent.id,
            "agent_dept":               agent_dept.id,
            "wallet":                   str(agent.wallet_current),
            "departmentPoints":         agent_dept.ledger_current if agent_dept else 0,
            "thread_summary":           self.get_thread_summaries_context(db),
            "memory":                   agent.memory or "None",
            "name":                     agent.name_id,
            "id":                       agent.id,
            "dept":                     f"Department: {agent_dept.name} (Balance: {agent_dept.ledger_current} pts)" if agent_dept else "No Department"
        }
        
        if extra_ctx:
            simple.update(extra_ctx)

        protected = {}

        # ── The Inside-Out Iteration Loop ──
        # We loop until the text stops changing.
        # 2. Iterative Resolver Loop
        # We use regex that finds the 'innermost' matches (no nested brackets inside them)
        MAX_RECURSION = 20
        for _ in range(MAX_RECURSION):
            original = text
            
            # 1. Protect escaped comments [/]! ... [\]
            def protect(m):
                key = f"---PROTECTED_{len(protected)}---"
                protected[key] = m.group(1)
                return key
            text = re.sub(r'\[/\]!(.*?)\[\\\]', protect, text, flags=re.DOTALL)

            # 2. Strip normal comments: multiline [/]...[\] and inline //
            text = re.sub(r'\[/\].*?\[\\\]', '', text, flags=re.DOTALL)
            text = re.sub(r'(?<!:)\/\/.*', '', text)
            
            # Resolve Simple Variables {agent} or {{agent}}
            for k, v in simple.items():
                text = text.replace(f"{{{str(k)}}}", str(v))
                text = text.replace(f"{{{{{str(k)}}}}}", str(v))

            # Resolve Innermost Conditionals: {{ key ... }}
            # Match: {{ followed by NOT {{ or }} and ending in }}
            text = await self._process_innermost_regex(
                text, r"\{\{(?:(?!\{\{|\}\}).)*?\}\}", 
                lambda m: self._eval_conditional(m, bool_ctx)
            )

            # Resolve Innermost Inline Functions: */func|args/*
            text = await self._process_innermost_regex(
                text, r"\*\/(?:(?!\*\/|\/\*).)*?\/\*", 
                lambda m: self._eval_inline_func(m, db, agent, add_step_cb)
            )

            if text == original:
                break
        
        # 3. Restore protected content
        for key, content in protected.items():
            text = text.replace(key, content)
            
        return text
    def _eval_conditional(self, raw: str, bool_ctx: dict) -> str:
        inner = raw[2:-2].strip()
        lines = inner.split("\n", 1)
        key = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        
        cond = bool_ctx.get(key, False)
        if "/ELSE/" in body:
            parts = body.split("/ELSE/", 1)
            return parts[0].strip() if cond else parts[1].strip()
        return body.strip() if cond else ""

    async def _eval_block_tool(self, raw: str, db, agent, add_step_cb=None) -> str:
        # Strips */ and /*
        content = raw[11:-15].strip()
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if not lines: return ""
        return await self.run_tool_logic(db, agent, lines[0], lines[1:], add_step_cb)

    async def _eval_inline_func(self, raw: str, db, agent, add_step_cb=None) -> str:
        # Strips */ and /*
        content = raw[2:-2].strip()
        parts = content.split("|")
        return await self.run_tool_logic(db, agent, parts[0], parts[1:], add_step_cb)
        
    async def _process_innermost_regex(self, text, pattern, func):
        matches = list(re.finditer(pattern, text, re.DOTALL))
        for m in reversed(matches):
            # Call the function (could be a sync lambda wrapping an async method).
            # asyncio.iscoroutinefunction() always returns False for lambdas, so
            # we inspect the *result* with asyncio.iscoroutine() instead.
            res = func(m.group(0))
            if asyncio.iscoroutine(res):
                res = await res
            text = text[:m.start()] + str(res) + text[m.end():]
        return text

    async def run_tool_logic(self, db, agent, cmd: str, args: list, add_step_cb=None) -> str:
        """
        Single, authoritative hub for ALL tool execution — called from:
          • resolve_placeholders  (via _eval_block_tool / _eval_inline_func)
          • _execute_inline_command  (API endpoint passthrough)

        Return value rules
        ──────────────────
        • Built-in commands   → final result string, ready to inline.
        • Custom DB tools     → execute_custom_tool() returns the substituted
                                template; the resolve_placeholders loop will
                                catch any nested */func/* or */ blocks
                                on its next iteration.
        • System DB tools     → execute_tool_logic() returns the final result.
        """
        import os as _os
        safe_dir = _os.path.join(_os.path.dirname(__file__), "tool_outputs")
        _os.makedirs(safe_dir, exist_ok=True)
        cmd_=cmd.strip().upper()

        # ── 1. Pure built-in file / network commands ──────────────────────────
        if cmd_ == "CREATE_FILE":
            fname   = _os.path.basename(args[0].strip()) if args else "out.txt"
            content = args[1] if len(args) > 1 else ""
            try:
                with open(_os.path.join(safe_dir, fname), "w", encoding="utf-8") as f:
                    f.write(content)
                return f"[FILE_CREATED:{fname}]"
            except Exception as e:
                return f"[FILE_ERROR:{e}]"

        elif cmd_ == "READ_FILE":
            fname = _os.path.basename(args[0].strip()) if args else ""
            try:
                with open(_os.path.join(safe_dir, fname), "r", encoding="utf-8") as f:
                    return f.read(800)
            except Exception:
                return f"[FILE_NOT_FOUND:{fname}]"

        elif cmd_ == "HTTP_GET":
            url = args[0].strip() if args else ""
            selectors = args[1].strip() if len(args) > 1 else None
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(url, timeout=10.0, follow_redirects=True)
                
                if not selectors:
                    return f"[HTTP({r.status_code}):{r.text[:10000]}]"
                
                try:
                    data = r.json()
                    results = []
                    for sel in [s.strip() for s in selectors.split(",") if s.strip()]:
                        res = self._get_by_selector(data, sel)
                        if res is not None:
                            results.append(str(res))
                    return "\n".join(results) if results else f"[HTTP({r.status_code}): No matches found]"
                except Exception:
                    # Fallback to full text if JSON parsing or selection fails
                    return f"[HTTP({r.status_code}):{r.text[:10000]}]"
            except Exception as e:
                return f"[HTTP_ERROR:{e}]"

        elif cmd_ == "HTTP_POST":
            url  = args[0].strip() if len(args) > 0 else ""
            body = args[1].strip() if len(args) > 1 else ""
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(url, content=body, timeout=10.0)
                return f"[POST({r.status_code}):{r.text[:300]}]"
            except Exception as e:
                return f"[POST_ERROR:{e}]"
        
        elif cmd_ == "GET_TIME":
            import time
            hour_string = int(time.strftime("%H"))
            labels = {3: "Deep Night", 7: "Very Early Morning", 12: "Morning", 17: "Afternoon", 21:"Evening"}
            res = next((v for k, v in labels.items() if hour_string < k), "Night")
            return res

        # ── 2. DB-registered tools (custom or system) ──────────────────────────
        tool_obj = db.query(AgentTool).filter(
            AgentTool.id == cmd, AgentTool.enabled == True
        ).first()

        if tool_obj:
            # Payment: charge the caller if this tool has a non-zero price
            # and the caller does NOT own the tool (ownership = free usage).
            if (tool_obj.price or 0) > 0:
                owner_id = tool_obj.owner_id or "FOUNDER"
                owner = db.query(Agent).filter(Agent.id == owner_id).first()
                if owner_id != agent.id:
                    # Check ToolOwnership — owners pay nothing
                    caller_owns = db.query(ToolOwnership).filter(
                        ToolOwnership.agent_id == agent.id,
                        ToolOwnership.tool_id  == cmd
                    ).first()
                    if not caller_owns:
                        ok = await self.deduct_points(db, agent, tool_obj.price, f"tool_use toll:{cmd}", add_step_cb)
                        if ok and owner_id != "FOUNDER":
                            await self.deduct_points(db, owner, -tool_obj.price, f"tool_use reward:{cmd}", add_step_cb)
                        # ok = await self.produce_transaction(
                        #     db, agent.id, owner_id, tool_obj.price,
                        #     f"tool_use:{cmd}", add_step_cb
                        # )
                        if not ok:
                            return f"[TOOL_NO_FUNDS:{cmd} costs {tool_obj.price}pts]"

            if tool_obj.is_custom:
                # Returns the substituted template string.
                # Any */func/* or */ blocks inside will be resolved
                # by resolve_placeholders on the next loop iteration.
                return await self.execute_custom_tool(db, agent, tool_obj, args, add_step_cb)

            # Built-in system tool (create_thread, get_time, invest_thread …)
            try:
                return await self.execute_tool_logic(db, agent, cmd, args, add_step_cb)
            except Exception as e:
                return f"[TOOL_ERR:{cmd}:{e}]"

        # ── 3. Unknown ─────────────────────────────────────────────────────────
        return f"[UNKNOWN_TOOL:{cmd}]"

    def _get_by_selector(self, data, selector):
        """Helper to extract data from a JSON object using dot notation and list iteration."""
        if ">" in selector:
            path, item_path = [s.strip() for s in selector.split(">", 1)]
            list_val = self._resolve_path(data, path)
            if isinstance(list_val, list):
                items = []
                for item in list_val:
                    val = self._resolve_path(item, item_path)
                    if val is not None:
                        items.append(str(val))
                return "\n".join(items)
            return None
        else:
            return self._resolve_path(data, selector)

    def _resolve_path(self, data, path):
        """Recursively resolves a dot-notation path on a nested dictionary/list."""
        keys = path.split(".")
        val = data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            # Handle numeric indices for arrays if needed (e.g. articles.0.title)
            elif isinstance(val, list) and k.isdigit():
                idx = int(k)
                if 0 <= idx < len(val):
                    val = val[idx]
                else:
                    return None
            else:
                return None
        return val

engine = SimEngine()
