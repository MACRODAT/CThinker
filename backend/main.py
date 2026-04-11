from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

import models, schemas, database
from engine import engine as sim_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    db = database.SessionLocal()
    seed_db(db)
    db.close()

    engine_task = asyncio.create_task(sim_engine.start())
    print("Simulation engine started")

    yield  # app runs here

    # --- SHUTDOWN ---
    sim_engine.stop()
    engine_task.cancel()
    print("Simulation engine stopped")


app = FastAPI(title="CThinker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)

def seed_db(db: Session):
    if db.query(models.PromptTemplate).first() is None:
        default_user_prompt = "TASK: Describe 1 definitive action you take. End exactly with [MEM: note] where note is an updated memory < 150 chars. Output only the final action with the mem tag."
        templates = [
            models.PromptTemplate(id="Creator", name="Creator", system_prompt="You are a creative agent focused on brainstorming and generating novel concepts.", user_prompt_template=default_user_prompt),
            models.PromptTemplate(id="Points Accounter", name="Points Accounter", system_prompt="You are an analytical agent focused on resource management, efficiency and budget constraints.", user_prompt_template=default_user_prompt),
            models.PromptTemplate(id="Invester", name="Investor", system_prompt="You are a strategic agent evaluating logical investments and maximizing long-term value.", user_prompt_template=default_user_prompt),
            models.PromptTemplate(id="Custom", name="Custom", system_prompt="You act logically, precisely according to your given parameters.", user_prompt_template=default_user_prompt),
        ]
        db.add_all(templates)
        db.commit()

    if db.query(models.Setting).first() is None:
        settings = [
            models.Setting(key="app_name", value="CThinker")
        ]
        db.add_all(settings)
        db.commit()

    if db.query(models.Department).first() is None:
        depts = [
            models.Department(id="HF", name="Health & Wellness", color="#4ade80"),
            models.Department(id="ING", name="Engineering", color="#22d3ee"),
            models.Department(id="STP", name="Strategic Planning", color="#fb923c"),
            models.Department(id="UIT", name="Useful Intelligence", color="#c084fc"),
            models.Department(id="FIN", name="Financing", color="#fbbf24")
        ]
        db.add_all(depts)
        db.commit()

        agents = [
            models.Agent(id="ATLAS", name_id="Atlas Prime", department_id="ING", is_ceo=True, ticks=22, mode="Creator"),
            models.Agent(id="VERA", name_id="Vera Nexus", department_id="STP", is_ceo=True, ticks=35, mode="Points Accounter"),
            models.Agent(id="KIRO", name_id="Kiro Banks", department_id="FIN", is_ceo=True, ticks=28, mode="Invester"),
            models.Agent(id="SANA", name_id="Sana Vell", department_id="HF", is_ceo=True, ticks=50, mode="Creator"),
            models.Agent(id="ORYN", name_id="Oryn Flux", department_id="UIT", is_ceo=True, ticks=18, mode="Custom"),
            models.Agent(id="PIKE", name_id="Pike Render", department_id="ING", is_ceo=False, ticks=60, mode="Creator"),
            models.Agent(id="MIRI", name_id="Miri Solv", department_id="FIN", is_ceo=False, ticks=45, mode="Invester"),
            models.Agent(id="TOVA", name_id="Tova Bright", department_id="UIT", is_ceo=False, ticks=80, mode="Points Accounter"),
        ]
        db.add_all(agents)
        db.commit()

# @app.on_event("startup")
# async def startup_event():
#     db = database.SessionLocal()
#     seed_db(db)
#     db.close()
    
#     # Start engine loop
#     asyncio.create_task(sim_engine.start())

# @app.on_event("shutdown")
# def shutdown_event():
#     sim_engine.stop()



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sim_engine.subscribers.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in sim_engine.subscribers:
            sim_engine.subscribers.remove(websocket)

@app.get("/api/state")
def get_state(db: Session = Depends(database.get_db)):
    depts = db.query(models.Department).all()
    agents = db.query(models.Agent).all()
    threads = db.query(models.Thread).all()
    prompts = db.query(models.PromptTemplate).all()
    settings = db.query(models.Setting).all()
    
    dept_ledgers = db.query(models.LogLedger).all()
    agent_actions = db.query(models.LogAction).order_by(models.LogAction.id.desc()).all()
    thread_msgs = db.query(models.Message).all()

    state_departments = {}
    for d in depts:
        logs = [{"time": l.time, "who": l.who, "amount": l.amount} for l in dept_ledgers if l.department_id == d.id]
        ag_ids = [a.id for a in agents if a.department_id == d.id]
        ceo = next((a.id for a in agents if a.department_id == d.id and a.is_ceo), None)
        state_departments[d.id] = {
            "name_id": d.id, "name": d.name, "color": d.color,
            "ledger": {"current": d.ledger_current, "log": logs},
            "ceo_name_id": ceo, "agents": ag_ids
        }

    state_agents = {}
    for a in agents:
        acts = [{"when": act.when, "what": act.what, "points": act.points} for act in agent_actions if act.agent_id == a.id]
        own_t = [t.id for t in threads if t.owner_agent_id == a.id]
        state_agents[a.id] = {
            "name_id": a.name_id, "born": a.born, "department": a.department_id,
            "is_ceo": a.is_ceo, "ticks": a.ticks, "wallet": {"current": a.wallet_current, "log": []},
            "mode": a.mode, "next_mode": a.next_mode, "custom_prompt": a.custom_prompt,
            "log_actions": acts, "memory": a.memory, "own_threads": own_t
        }

    state_threads = {}
    for t in threads:
        msgs = [{"when": m.when, "who": m.who, "what": m.what, "points": m.points} for m in thread_msgs if m.thread_id == t.id]
        state_threads[t.id] = {
            "id": t.id, "owner_department": t.owner_department_id, "owner_agent": t.owner_agent_id,
            "topic": t.topic, "aim": t.aim, "status": t.status, "created": t.created,
            "point_wallet": {"budget": t.budget, "log": []}, "messages_log": msgs
        }

    return {
        "departments": state_departments,
        "agents": state_agents,
        "threads": state_threads,
        "prompts": {p.id: {"id": p.id, "name": p.name, "system_prompt": p.system_prompt, "user_prompt_template": p.user_prompt_template, "custom_directives": p.custom_directives} for p in prompts},
        "settings": {s.key: s.value for s in settings}
    }

@app.post("/api/threads", response_model=schemas.ThreadResponse)
def create_thread(thread: schemas.ThreadCreate, db: Session = Depends(database.get_db)):
    # outline.md: "(COST: 25 Points for Memo, 100 POINTS for Strategy, 100 POINTS for endeavor)"
    costs = {"Memo": 25, "Strategy": 100, "Endeavor": 100}
    cost = costs.get(thread.aim, 25)
    
    agent = db.query(models.Agent).filter(models.Agent.id == thread.owner_agent_id).first()
    if not agent:
        return {"error": "Agent not found"}
        
    dept = agent.department
    if dept and dept.ledger_current < cost:
        return {"error": f"Not enough department points (need {cost})"}
    elif not dept and agent.wallet_current < cost:
        return {"error": f"Not enough agent points (need {cost})"}
        
    if dept:
        dept.ledger_current -= cost
    else:
        agent.wallet_current -= cost
        
    import uuid
    tid = str(uuid.uuid4())[:8].upper()
    db_thread = models.Thread(
        id=tid,
        topic=thread.topic,
        aim=thread.aim,
        owner_agent_id=agent.id,
        owner_department_id=dept.id if dept else None,
        budget=cost
    )
    db.add(db_thread)
    db.commit()
    db.refresh(db_thread)
    return db_thread

@app.post("/api/threads/{thread_id}/messages")
def create_message(thread_id: str, message: schemas.MessageCreate, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t:
        return {"error": "Thread not found"}
        
    agent = db.query(models.Agent).filter(models.Agent.id == message.who).first()
    if not agent:
        return {"error": "Agent not found"}
        
    is_owner = (t.owner_agent_id == agent.id)
    cost = 0 if is_owner else 1
    
    if not is_owner and agent.wallet_current < cost:
        return {"error": "Not enough points"}
        
    if not is_owner:
        agent.wallet_current -= cost
        
    msg = models.Message(thread_id=thread_id, who=agent.id, what=message.what, points=-cost)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

@app.post("/api/threads/{thread_id}/approve")
def approve_thread(thread_id: str, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: return {"error": "Thread not found"}
    if t.status in ["REJECTED", "FROZEN", "APPROVED"]: return {"error": "Invalid state"}
    
    reward = t.budget * 10
    owner_share = int(reward * 0.7)
    dept_share = reward - owner_share
    
    t.status = "APPROVED"
    owner = db.query(models.Agent).filter(models.Agent.id == t.owner_agent_id).first()
    if owner: owner.wallet_current += owner_share
    if t.owner_department_id:
        dept = db.query(models.Department).filter(models.Department.id == t.owner_department_id).first()
        if dept: dept.ledger_current += dept_share
    
    db.commit()
    return {"status": "success", "reward": reward}

@app.post("/api/threads/{thread_id}/reject")
def reject_thread(thread_id: str, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: return {"error": "Thread not found"}
    t.status = "REJECTED"
    t.budget = 0
    db.commit()
    return {"status": "success"}

@app.post("/api/departments/{dept_id}/points")
def add_dept_points(dept_id: str, payload: dict, db: Session = Depends(database.get_db)):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept: return {"error": "Dept not found"}
    amount = payload.get("amount", 0)
    dept.ledger_current += amount
    db.add(models.LogLedger(department_id=dept.id, why="top-up", who="FOUNDER", amount=amount))
    db.commit()
    return {"status": "success"}

@app.get("/api/threads/{thread_id}/messages")
def get_messages(thread_id: str, db: Session = Depends(database.get_db)):
    return db.query(models.Message).filter(models.Message.thread_id == thread_id).all()

@app.get("/api/prompts")
def get_prompts(db: Session = Depends(database.get_db)):
    return db.query(models.PromptTemplate).all()

@app.put("/api/prompts/{prompt_id}")
def update_prompt(prompt_id: str, payload: dict, db: Session = Depends(database.get_db)):
    p = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not p: return {"error": "Prompt not found"}
    if "name" in payload: p.name = payload["name"]
    if "system_prompt" in payload: p.system_prompt = payload["system_prompt"]
    if "user_prompt_template" in payload: p.user_prompt_template = payload["user_prompt_template"]
    if "custom_directives" in payload: p.custom_directives = payload["custom_directives"]
    db.commit()
    return {"status": "success"}

@app.get("/api/settings")
def get_settings(db: Session = Depends(database.get_db)):
    return db.query(models.Setting).all()

@app.put("/api/settings/{setting_key}")
def update_setting(setting_key: str, payload: dict, db: Session = Depends(database.get_db)):
    s = db.query(models.Setting).filter(models.Setting.key == setting_key).first()
    if not s:
        s = models.Setting(key=setting_key, value=payload.get("value", ""))
        db.add(s)
    else:
        if "value" in payload:
            s.value = payload["value"]
    db.commit()
    return {"status": "success"}

@app.put("/api/agents/{agent_id}")
def update_agent(agent_id: str, payload: dict, db: Session = Depends(database.get_db)):
    a = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not a: return {"error": "Agent not found"}
    if "mode" in payload: a.mode = payload["mode"]
    if "custom_prompt" in payload: a.custom_prompt = payload["custom_prompt"]
    if "memory" in payload: a.memory = payload["memory"]
    db.commit()
    return {"status": "success"}

@app.get("/api/test-ollama")
async def test_ollama(db: Session = Depends(database.get_db)):
    s = db.query(models.Setting).filter(models.Setting.key == "ollama_model").first()
    model_name = s.value if s else "gemma4:e4b"
    
    s_srv = db.query(models.Setting).filter(models.Setting.key == "ollama_server").first()
    server_url = s_srv.value if s_srv else "http://localhost:11434"
    if not server_url.endswith("/api/generate"):
        server_url = server_url.rstrip("/") + "/api/generate"
        
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(server_url, json={
                "model": model_name,
                "prompt": "Hello! Respond with one short sentence.",
                "stream": False
            }, timeout=90.0)
            if resp.status_code == 200:
                resp_text = resp.json().get("response", "")
                return {"status": "success", "message": f"Connection successful! Model '{model_name}' responded.", "llm_response": resp_text}
            else:
                body = resp.text
                return {"status": "error", "message": f"Ollama returned HTTP {resp.status_code}: {body[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}

@app.get("/api/ollama-models")
async def get_ollama_models(db: Session = Depends(database.get_db)):
    s_srv = db.query(models.Setting).filter(models.Setting.key == "ollama_server").first()
    base_url = s_srv.value if s_srv else "http://localhost:11434"
    tags_url = base_url.rstrip("/") + "/api/tags"
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(tags_url, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                model_names = [m["name"] for m in data.get("models", [])]
                return {"status": "success", "models": model_names}
            else:
                return {"status": "error", "models": [], "message": f"Ollama returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "models": [], "message": str(e)}

# --- Prompt Entries (reusable saved snippets) ---

@app.get("/api/prompt-entries")
def get_prompt_entries(db: Session = Depends(database.get_db)):
    return db.query(models.CustomPromptEntry).order_by(models.CustomPromptEntry.id.desc()).all()

@app.post("/api/prompt-entries", response_model=schemas.CustomPromptEntryResponse)
def create_prompt_entry(entry: schemas.CustomPromptEntryCreate, db: Session = Depends(database.get_db)):
    e = models.CustomPromptEntry(title=entry.title, body=entry.body)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e

@app.delete("/api/prompt-entries/{entry_id}")
def delete_prompt_entry(entry_id: int, db: Session = Depends(database.get_db)):
    e = db.query(models.CustomPromptEntry).filter(models.CustomPromptEntry.id == entry_id).first()
    if not e: return {"error": "Entry not found"}
    db.delete(e)
    db.commit()
    return {"status": "success"}
