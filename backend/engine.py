import asyncio
import httpx
import datetime
import json
import re
import traceback
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    Department, Agent, Thread, LogAction, LogLedger,
    PromptTemplate, Setting, AgentTool, SystemLog
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
            prefix = s_prefix.value if s_prefix else "AVAILABLE TOOLS:\nNote: include the exact [TOOL: name(args)] tag to use a tool."
            tools_block = (
                prefix + "\n" + "\n".join([f"- {t.description}" for t in enabled_tools])
                if enabled_tools else "No tools currently available."
            )

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

                # ── Point deduction ──────────────────────────────────────────
                can_tick = False
                if dept:
                    if dept.ledger_current >= 1:
                        dept.ledger_current -= 1
                        can_tick = True
                        db.add(LogLedger(department_id=dept.id, who=agent.id, why="tick", amount=-1))
                        await self.log(db, "POINT", "AGENT", "TICK_COST", {
                            "agent": agent.name_id,
                            "dept": dept.name,
                            "dept_balance_after": dept.ledger_current
                        }, agent_id=agent.id, dept_id=dept.id)
                    else:
                        await self.log(db, "WARN", "AGENT", "TICK_SKIPPED_NO_DEPT_POINTS", {
                            "agent": agent.name_id,
                            "dept": dept.name,
                            "balance": dept.ledger_current
                        }, agent_id=agent.id, dept_id=dept.id)
                else:
                    if agent.wallet_current >= 1:
                        agent.wallet_current -= 1
                        can_tick = True
                        await self.log(db, "POINT", "AGENT", "WALLET_DEDUCT", {
                            "agent": agent.name_id,
                            "amount": -1,
                            "wallet_after": agent.wallet_current
                        }, agent_id=agent.id)
                    else:
                        await self.log(db, "WARN", "AGENT", "TICK_SKIPPED_NO_WALLET", {
                            "agent": agent.name_id,
                            "balance": agent.wallet_current
                        }, agent_id=agent.id)

                if not can_tick:
                    continue

                # ── Build agent prompt ───────────────────────────────────────
                active_threads = db.query(Thread).filter(
                    Thread.status.in_(["OPEN", "ACTIVE"])
                ).limit(3).all()
                thread_ctx = "\n".join(
                    [f'- {t.id} : "{t.topic}" [{t.aim}] pts={t.budget}' for t in active_threads]
                ) or "none"

                dept_name = dept.name if dept else "freelance"
                mode_template = db.query(PromptTemplate).filter(
                    PromptTemplate.id == agent.mode
                ).first()
                system_instruction = mode_template.system_prompt if mode_template else "You act logically."

                base_prompt = (
                    f"System: {system_instruction}\n"
                    f"You are {agent.name_id}, operating in {dept_name}.\n"
                    f"Memory Context: {agent.memory}\n"
                    f"Active Threads:\n{thread_ctx}\n\n"
                    f"{tools_block}\n\n"
                )
                if mode_template and mode_template.custom_directives:
                    base_prompt += f"Mode Directives:\n{mode_template.custom_directives}\n\n"
                if agent.custom_prompt:
                    base_prompt += f"Personal Directives:\n{agent.custom_prompt}\n\n"

                user_template = (
                    mode_template.user_prompt_template
                    if mode_template and mode_template.user_prompt_template
                    else "TASK: Describe 1 definitive action you take. End exactly with [MEM: note] where note is an updated memory < 150 chars."
                )
                base_prompt += user_template

                all_modes = [pt.id for pt in db.query(PromptTemplate).all()]

                await self.log(db, "TICK", "AGENT", "AGENT_TICK", {
                    "agent": agent.name_id,
                    "mode": agent.mode,
                    "ticks_every": agent.ticks,
                    "counter": self.counter,
                    "memory": agent.memory,
                    "dept": dept_name,
                }, agent_id=agent.id, dept_id=dept.id if dept else None)

                task_coros.append(
                    self.run_agent_llm(agent.id, base_prompt, dept.id if dept else None, all_modes)
                )

            db.commit()

            if task_coros:
                await asyncio.gather(*task_coros)

        except Exception as e:
            print(f"[ENGINE] tick error: {e}")
            traceback.print_exc()
        finally:
            db.close()

    # ── Agent LLM runner ─────────────────────────────────────────────────────

    async def run_agent_llm(self, agent_id: str, prompt: str,
                            dept_id: str | None, all_modes: list):
        db: Session = SessionLocal()
        t_start = datetime.datetime.now()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return

            s_model  = db.query(Setting).filter(Setting.key == "ollama_model").first()
            s_server = db.query(Setting).filter(Setting.key == "ollama_server").first()
            used_model  = s_model.value  if s_model  else "gemma3:4b"
            server_base = s_server.value if s_server else "http://localhost:11434"
            gen_url = server_base.rstrip("/") + "/api/generate"

            # ── Log LLM call start ───────────────────────────────────────────
            await self.log(db, "LLM", "LLM", "LLM_CALL_START", {
                "agent": agent.name_id,
                "model": used_model,
                "server": server_base,
                "prompt_chars": len(prompt),
                "prompt_preview": prompt[:400],
            }, agent_id=agent_id, dept_id=dept_id)
            db.commit()

            # ── Call Ollama ──────────────────────────────────────────────────
            text = ""
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(gen_url, json={
                        "model": used_model,
                        "prompt": prompt,
                        "stream": False
                    }, timeout=90.0)
                    resp.raise_for_status()
                    text = resp.json().get("response", "")
                    elapsed = round((datetime.datetime.now() - t_start).total_seconds(), 2)

                    await self.log(db, "LLM", "LLM", "LLM_CALL_DONE", {
                        "agent": agent.name_id,
                        "model": used_model,
                        "elapsed_s": elapsed,
                        "response_chars": len(text),
                        "response_preview": text[:400],
                    }, agent_id=agent_id, dept_id=dept_id)

            except Exception as e:
                elapsed = round((datetime.datetime.now() - t_start).total_seconds(), 2)
                text = f"[ERROR – LLM unreachable] [MEM: {agent.memory}]"
                await self.log(db, "ERROR", "LLM", "LLM_CALL_ERROR", {
                    "agent": agent.name_id,
                    "model": used_model,
                    "error": str(e),
                    "elapsed_s": elapsed,
                    "tip": "Check ollama_server / ollama_model in Settings, or run: ollama serve"
                }, agent_id=agent_id, dept_id=dept_id)
                print(f"[LLM] {agent_id}: {e}")

            # ── Parse response ───────────────────────────────────────────────
            mem_match = re.search(r"\[MEM:\s*(.+?)\]", text)
            new_mem = mem_match.group(1)[:150] if mem_match else agent.memory
            act = re.sub(r"\[MEM:.+?\]", "", text).strip()

            # ── Tool execution ───────────────────────────────────────────────
            tool_res = await self.handle_tools(db, agent, act)
            if tool_res:
                act += f" ({tool_res})"

            agent.memory = new_mem
            log_action = LogAction(agent_id=agent.id, what=act)
            db.add(log_action)

            await self.log(db, "INFO", "AGENT", "AGENT_ACTION", {
                "agent": agent.name_id,
                "action": act[:500],
                "memory_updated": new_mem,
            }, agent_id=agent_id, dept_id=dept_id)

            # ── Mode self-selection ──────────────────────────────────────────
            if all_modes and len(all_modes) > 1:
                try:
                    modes_str = ", ".join(all_modes)
                    mode_prompt = (
                        f"You are {agent.name_id}. Your last action: {act[:200]}\n"
                        f"Available operating modes: {modes_str}\n"
                        f"Based on your last action, which mode should you adopt NEXT?\n"
                        f"Reply with ONLY the exact mode name from the list above, nothing else."
                    )
                    async with httpx.AsyncClient() as client:
                        mr = await client.post(gen_url, json={
                            "model": used_model, "prompt": mode_prompt, "stream": False
                        }, timeout=30.0)
                        chosen = mr.json().get("response", "").strip().strip('"').strip("'")
                    if chosen in all_modes:
                        agent.next_mode = chosen
                        await self.log(db, "INFO", "AGENT", "NEXT_MODE_SELECTED", {
                            "agent": agent.name_id,
                            "current_mode": agent.mode,
                            "selected_next": chosen,
                        }, agent_id=agent_id, dept_id=dept_id)
                except Exception as e:
                    await self.log(db, "WARN", "AGENT", "MODE_SELECT_ERROR", {
                        "agent": agent.name_id, "error": str(e)
                    }, agent_id=agent_id, dept_id=dept_id)

            db.commit()

            await self.broadcast({
                "type": "feed",
                "feed_item": {
                    "id": log_action.id,
                    "agent": agent.name_id,
                    "dept": dept_id,
                    "msg": act[:120]
                }
            })

        except Exception as e:
            print(f"[ENGINE] run_agent_llm({agent_id}): {e}")
            traceback.print_exc()
        finally:
            db.close()

    # ── Tool handler ─────────────────────────────────────────────────────────

    async def handle_tools(self, db, agent, text: str):
        tool_match = re.search(r"\[TOOL:\s*(\w+)\((.*?)\)\]", text)
        if not tool_match:
            return None

        tool_name = tool_match.group(1)
        args_raw  = tool_match.group(2).strip()

        def parse_args(s):
            if not s: return []
            import csv
            import io
            f = io.StringIO(s)
            reader = csv.reader(f, skipinitialspace=True, delimiter=',', quotechar='"')
            try:
                line = next(reader)
                # Strip quotes AND remove any "key=" prefixes agents might output
                return [re.sub(r'^(\w+)=', '', arg.strip().strip("'").strip('"')) for arg in line]
            except StopIteration:
                return []

        args = parse_args(args_raw)
        args_str = ", ".join(args) # For logging

        # Validate tool is registered & enabled
        tool_entry = db.query(AgentTool).filter(AgentTool.id == tool_name).first()
        if not tool_entry or not tool_entry.enabled:
            await self.log(db, "WARN", "TOOL", "TOOL_DISABLED_OR_UNKNOWN", {
                "tool": tool_name, "agent": agent.name_id
            }, agent_id=agent.id)
            return f"TOOL_ERROR: '{tool_name}' is disabled or unknown."

        await self.log(db, "TOOL", "TOOL", "TOOL_INVOKE", {
            "tool": tool_name, "args": args_str, "agent": agent.name_id
        }, agent_id=agent.id)

        result = None

        # ── modify_own_tick ────────────────────────────────────────────────────
        if tool_name == "modify_own_tick":
            try:
                new_val = int(args_str)
                conflict = db.query(Agent).filter(
                    Agent.ticks == new_val, Agent.id != agent.id
                ).first()
                if not conflict and new_val > 0:
                    old_val = agent.ticks
                    agent.ticks = new_val
                    result = f"CLOCK_SYNC: Tick adjusted {old_val}s → {new_val}s."
                else:
                    result = f"CLOCK_ERROR: Frequency {new_val}s is occupied or invalid."
            except Exception:
                result = "CLOCK_ERROR: Invalid parameter."

        # ── get_time ──────────────────────────────────────────────────────────
        elif tool_name == "get_time":
            now_local = datetime.datetime.now()
            now_utc   = datetime.datetime.now(datetime.timezone.utc)
            result = (
                f"TIME: {now_local.strftime('%A, %Y-%m-%d %H:%M:%S')} "
                f"(UTC {now_utc.strftime('%H:%M:%S')})"
            )

        # ── get_weather ───────────────────────────────────────────────────────
        elif tool_name == "get_weather":
            city = args_str or "Casablanca"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"https://wttr.in/{city}?format=3",
                        timeout=10.0,
                        headers={"User-Agent": "CThinker/1.0 curl/8.0"}
                    )
                    result = f"WEATHER: {resp.text.strip()}"
            except Exception as e:
                result = f"WEATHER_ERROR: {str(e)}"

        # ── create_thread ──────────────────────────────────────────────────────
        elif tool_name == "create_thread":
            try:
                if len(args) < 2:
                    result = "THREAD_ERROR: Missing parameters. Use: create_thread(topic, aim)."
                else:
                    topic, aim = args[0], args[1].strip().capitalize()
                    costs = {"Memo": 25, "Strategy": 100, "Endeavor": 100}
                    cost  = costs.get(aim, 25)
                    
                    if agent.wallet_current < cost:
                        result = f"THREAD_ERROR: Insufficient wallet points (need {cost})."
                    else:
                        import uuid
                        tid = str(uuid.uuid4())[:8].upper()
                        new_thread = Thread(
                            id=tid, topic=topic, aim=aim,
                            owner_agent_id=agent.id,
                            owner_department_id=agent.department_id,
                            budget=cost, status="OPEN"
                        )
                        agent.wallet_current -= cost
                        db.add(new_thread)
                        result = f"THREAD_CREATED: ID={tid}, Topic='{topic}', Aim={aim}, Cost={cost}."
            except Exception as e:
                result = f"THREAD_ERROR: {str(e)}"

        # ── invest_thread ──────────────────────────────────────────────────────
        elif tool_name == "invest_thread":
            try:
                if len(args) < 2:
                    result = "INVEST_ERROR: Missing parameters. Use: invest_thread(thread_id, budget)."
                else:
                    tid, amount = args[0].strip().upper(), int(args[1].strip())
                    target_thread = db.query(Thread).filter(Thread.id == tid).first()
                    if not target_thread:
                        result = f"INVEST_ERROR: Thread {tid} not found."
                    elif amount <= 0:
                        result = "INVEST_ERROR: Amount must be positive."
                    elif agent.wallet_current < amount:
                        result = f"INVEST_ERROR: Insufficient wallet points (need {amount})."
                    else:
                        agent.wallet_current -= amount
                        target_thread.budget += amount
                        result = f"INVEST_SUCCESS: Invested {amount} pts into Thread {tid}."
            except Exception:
                result = "INVEST_ERROR: Invalid parameter."

        # ── post_in_thread ─────────────────────────────────────────────────────
        elif tool_name == "post_in_thread":
            try:
                if len(args) < 2:
                    result = "POST_ERROR: Missing parameters. Use: post_in_thread(thread_id, content)."
                else:
                    from models import Message
                    tid, content = args[0].strip().upper(), args[1].strip()
                    target_thread = db.query(Thread).filter(Thread.id == tid).first()
                    if not target_thread:
                        result = f"POST_ERROR: Thread {tid} not found."
                    else:
                        is_owner = (target_thread.owner_agent_id == agent.id)
                        cost = 0 if is_owner else 1
                        if agent.wallet_current < cost:
                            result = f"POST_ERROR: Insufficient wallet points (need {cost})."
                        else:
                            agent.wallet_current -= cost
                            new_msg = Message(thread_id=tid, who=agent.id, what=content, points=-cost)
                            db.add(new_msg)
                            result = f"POST_SUCCESS: Contributed to Thread {tid}."
            except Exception as e:
                result = f"POST_ERROR: {str(e)}"

        # ── get_news ──────────────────────────────────────────────────────────
        elif tool_name == "get_news":
            try:
                topic = args[0] if args else "world"
                from xml.etree import ElementTree as ET
                if topic.lower() in ("world", "general", ""):
                    rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
                else:
                    rss_url = (
                        f"https://news.google.com/rss/search"
                        f"?q={topic}&hl=en-US&gl=US&ceid=US:en"
                    )
                async with httpx.AsyncClient() as client:
                    resp = await client.get(rss_url, timeout=12.0, follow_redirects=True)
                root = ET.fromstring(resp.text)
                items = root.findall(".//item")[:4]
                headlines = []
                for item in items:
                    t_el = item.find("title")
                    if t_el is not None and t_el.text:
                        h = re.sub(r"\s*-\s*[^-]+$", "", t_el.text).strip()
                        if h:
                            headlines.append(h)
                result = (
                    f"NEWS({topic}): " + " | ".join(headlines)
                    if headlines
                    else f"NEWS: No headlines found for '{topic}'"
                )
            except Exception as e:
                result = f"NEWS_ERROR: {str(e)}"

        # ── get_threads ────────────────────────────────────────────────────────
        elif tool_name == "get_threads":
            try:
                # Filter indices: 0=status, 1=department, 2=owner
                f_status = args[0].strip().upper() if len(args) > 0 and args[0].strip().lower() != "none" else None
                f_dept   = args[1].strip().upper() if len(args) > 1 and args[1].strip() else None
                f_owner  = args[2].strip().upper() if len(args) > 2 and args[2].strip() else None
                
                q = db.query(Thread)
                if f_status: q = q.filter(Thread.status == f_status)
                if f_dept:   q = q.filter(Thread.owner_department_id == f_dept)
                if f_owner:  q = q.filter(Thread.owner_agent_id == f_owner)
                
                threads = q.order_by(Thread.created.desc()).limit(100).all()
                if not threads:
                    result = "THREADS_LIST: No threads matching filters."
                else:
                    lines = [f"{t.id} | {t.topic} | {t.aim} | {t.budget}pt | {t.status}" for t in threads]
                    result = "THREADS_LIST:\n" + "\n".join(lines)
            except Exception as e:
                result = f"THREADS_ERROR: {str(e)}"

        # ── Unknown ────────────────────────────────────────────────────────────
        else:
            result = f"TOOL_ERROR: Handler for '{tool_name}' not implemented."

        if result:
            await self.log(db, "TOOL", "TOOL", "TOOL_RESULT", {
                "tool": tool_name, "args": args_str,
                "result": result, "agent": agent.name_id
            }, agent_id=agent.id)

        return result


engine = SimEngine()
