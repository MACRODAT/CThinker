import asyncio
import httpx
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Department, Agent, Thread, LogAction, LogLedger, PromptTemplate, Setting
import datetime
import json

class SimEngine:
    def __init__(self):
        self.counter = 0
        self.running = False
        self.subscribers = [] # WebSockets

    async def start(self):
        self.running = True
        while self.running:
            await self.tick()
            await asyncio.sleep(1)

    def stop(self):
        self.running = False

    async def broadcast(self, message: dict):
        # We will iterate backwards or safely over subscribers and handle disconnected ones later in main.py
        for ws in list(self.subscribers):
            try:
                await ws.send_json(message)
            except Exception:
                self.subscribers.remove(ws)

    async def tick(self):
        self.counter += 1
        if self.counter >= 3600:
            self.counter = 0

        # Run DB logic
        db: Session = SessionLocal()
        try:
            # Find ticking agents
            # Since agents is small, fetch all and filter, or just query those matching tick
            agents = db.query(Agent).all()
            ticking_agents = [a for a in agents if a.ticks > 0 and self.counter % a.ticks == 0]

            if not ticking_agents:
                # Still broadcast heartbeat
                await self.broadcast({"type": "heartbeat", "counter": self.counter})
                return

            tick_events = []
            
            for agent in ticking_agents:
                dept = agent.department
                can_tick = False
                
                # Apply next_mode if set
                if agent.next_mode:
                    agent.mode = agent.next_mode
                    agent.next_mode = None
                
                # Check points
                if dept:
                    if dept.ledger_current >= 1:
                        dept.ledger_current -= 1
                        can_tick = True
                        db.add(LogLedger(department_id=dept.id, who=agent.id, why="tick", amount=-1))
                else:
                    if agent.wallet_current >= 1:
                        agent.wallet_current -= 1
                        can_tick = True

                if not can_tick:
                    continue

                # Prepare context for LLM
                active_threads = db.query(Thread).filter(Thread.status.in_(["OPEN", "ACTIVE"])).limit(3).all()
                thread_ctx = "\n".join([f'- "{t.topic}" [{t.aim}] pts={t.budget}' for t in active_threads]) or "none"
                dept_name = dept.name if dept else "freelance"
                
                # Fetch PromptTemplate via mode
                mode_template = db.query(PromptTemplate).filter(PromptTemplate.id == agent.mode).first()
                system_instruction = mode_template.system_prompt if mode_template else "You act logically."

                # Construct prompt
                base_prompt = (
                    f"System: {system_instruction}\n"
                    f"You are {agent.name_id}, operating in {dept_name}.\n"
                    f"Memory Context: {agent.memory}\n"
                    f"Active Threads:\n{thread_ctx}\n"
                )
                
                # Inject per-mode custom directives
                if mode_template and mode_template.custom_directives:
                    base_prompt += f"\nMode Directives:\n{mode_template.custom_directives}\n"
                    
                # Inject per-agent custom prompt override
                if agent.custom_prompt:
                    base_prompt += f"\nPersonal Directives:\n{agent.custom_prompt}\n"
                    
                user_template = mode_template.user_prompt_template if (mode_template and mode_template.user_prompt_template) else "TASK: Describe 1 definitive action you take. End exactly with [MEM: note] where note is an updated memory < 150 chars. Output only the final action with the mem tag."
                base_prompt += f"\n{user_template}"

                # Build list of available mode IDs for self-selection
                all_modes = [pt.id for pt in db.query(PromptTemplate).all()]

                tick_events.append(self.run_agent_llm(db, agent.id, base_prompt, dept.id if dept else None, all_modes))

            db.commit()

            # Execute LLMs
            if tick_events:
                await asyncio.gather(*tick_events)
                
            await self.broadcast({"type": "heartbeat", "counter": self.counter})
            
        except Exception as e:
            print(f"Error in engine tick: {e}")
        finally:
            db.close()

    async def run_agent_llm(self, db_factory_ignore, agent_id, prompt, dept_id, all_modes=None):
        # We need a new session per task to avoid concurrent DB session issues if needed, or just one per tick loop. 
        # For simplicity, we just use one new session here
        db: Session = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return

            try:
                s_model = db.query(Setting).filter(Setting.key == "ollama_model").first()
                used_model = s_model.value if s_model else "gemma4:e4b"
                
                s_server = db.query(Setting).filter(Setting.key == "ollama_server").first()
                server_url = s_server.value if s_server else "http://localhost:11434"
                if not server_url.endswith("/api/generate"):
                    server_url = server_url.rstrip("/") + "/api/generate"
                
                async with httpx.AsyncClient() as client:
                    resp = await client.post(server_url, json={
                        "model": used_model,
                        "prompt": prompt,
                        "stream": False
                    }, timeout=10.0)
                    text = resp.json().get("response", "")
            except Exception as e:
                text = f"Analyzed situation internally... [MEM: {agent.memory}] (LLM err: {e})"
                print(text)
            import re
            mem_match = re.search(r"\[MEM:\s*(.+?)\]", text)
            new_mem = mem_match.group(1)[:150] if mem_match else agent.memory
            act = re.sub(r"\[MEM:.+?\]", "", text).strip()

            agent.memory = new_mem
            logra = LogAction(agent_id=agent.id, what=act)
            db.add(logra)

            # --- Mode self-selection ---
            if all_modes and len(all_modes) > 1:
                try:
                    modes_str = ", ".join(all_modes)
                    mode_prompt = (
                        f"You are {agent.name_id}. Your last action: {act[:200]}\n"
                        f"Available operating modes: {modes_str}\n"
                        f"Based on your last action and upcoming priorities, which mode should you adopt next?\n"
                        f"Reply with ONLY the exact mode name from the list above, nothing else."
                    )
                    s_model = db.query(Setting).filter(Setting.key == "ollama_model").first()
                    used_model = s_model.value if s_model else "gemma4:e4b"
                    s_server = db.query(Setting).filter(Setting.key == "ollama_server").first()
                    server_url = (s_server.value if s_server else "http://localhost:11434").rstrip("/") + "/api/generate"
                    async with httpx.AsyncClient() as client:
                        mode_resp = await client.post(server_url, json={
                            "model": used_model,
                            "prompt": mode_prompt,
                            "stream": False
                        }, timeout=30.0)
                        chosen = mode_resp.json().get("response", "").strip().strip('"').strip("'")
                    # Validate it's a real mode
                    if chosen in all_modes:
                        agent.next_mode = chosen
                except Exception as e:
                    print(f"Mode selection error for {agent_id}: {e}")

            db.commit()
            
            await self.broadcast({
                "type": "feed",
                "feed_item": {"id": logra.id, "agent": agent.name_id, "dept": dept_id, "msg": act[:100]}
            })

        finally:
            db.close()

engine = SimEngine()
