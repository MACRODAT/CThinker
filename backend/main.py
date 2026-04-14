from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
import asyncio
import httpx
import re

import models, schemas, database
from engine import engine as sim_engine



@asynccontextmanager
async def lifespan(app: FastAPI):
    db = database.SessionLocal()
    seed_db(db)
    db.close()
    engine_task = asyncio.create_task(sim_engine.start())
    print("[CThinker] Simulation engine started.")
    for route in app.routes:
        print(f"DEBUG_ROUTE: {route.path}")
    yield
    sim_engine.stop()
    engine_task.cancel()
    print("[CThinker] Simulation engine stopped.")


app = FastAPI(title="CThinker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



models.Base.metadata.create_all(bind=database.engine)


# @app.get("/api/debug/routes")
# def debug_routes():
#     return [{"path": r.path, "name": getattr(r, 'name', None), "type": str(type(r))} for r in app.routes]

# ── Seeder ───────────────────────────────────────────────────────────────────

def seed_db(db: Session):
    # ── Prompt templates ──────────────────────────────────────────────────────
    if db.query(models.PromptTemplate).first() is None:
        default_user = (
            "AGENT: {name} (ID: {id})\n"
            "WALLET: {wallet} pts | {dept}\n"
            "MEMORY: {memory}\n"
            "RECENT ACTIONS:\n{actions}\n\n"
            "{directives}\n\n"
            "{tools}\n\n"
            "MANDATORY FORMAT FOR STATE UPDATES AT THE END:\n"
            "[MEMORY]\nupdated_memory_content\n[END MEMORY]\n\n"
            "[MODE]\nnext_mode_id\n[END MODE]"
        )
        templates = [
        models.PromptTemplate(
            id="Creator",
            name="Creator / Actionist",
            system_prompt="You are a proactive agent focused on creation and project execution.",
            user_prompt_template="# STATUS\nName: {name}\nWallet: {wallet}pt\n{dept}\n\n# INSTRUCTIONS\n{directives}\n\n# RECENT ACTIVITY\n{actions}\n\n# AVAILABLE TICKETS\n{{available_tickets}}\n\n# PENDING INVITES\n{{pending_invitation}}\n\n# LAST INVITE STATUS\n{{invitation_status}}\n\n# TOOLS\n{tools}\n\n# MEMORY\n{memory}\n\nTASK: Generate strategy or take action.",
            custom_directives="- Identify opportunities\n- Create threads for new ideas\n- Invite collaborators to your threads.\n- Accept or Decline invitations promptly."
        ),
            models.PromptTemplate(
                id="Points Accounter", name="Points Accounter",
                system_prompt="You are an analytical agent focused on resource management, efficiency and budget constraints.",
                user_prompt_template=default_user),
            models.PromptTemplate(
                id="Invester", name="Investor",
                system_prompt="You are a strategic agent evaluating logical investments and maximizing long-term value.",
                user_prompt_template=default_user),
            models.PromptTemplate(
                id="Custom", name="Custom",
                system_prompt="You act logically, precisely according to your given parameters.",
                user_prompt_template=default_user),
            models.PromptTemplate(
                id="Chat", name="Direct Chat",
                system_prompt="You are in a private 1-on-1 chat with the Founder. Stay professional and helpful according to your role.",
                user_prompt_template=(
                    "THE FOUNDER SAYS: {message}\n\n"
                    "TASK: Respond directly and stay in character. You can use tools if needed.\n\n"
                    "TOOL CALLING FORMAT:\n"
                    "[CALL_TOOL]\n- tool_name\n- arg1\n[END_CALL_TOOL]\n\n"
                    "MANDATORY FORMAT FOR STATE UPDATES:\n"
                    "[MEMORY]\nupdated_memory_content\n[END MEMORY]\n\n"
                    "[MODE]\nnext_mode_id\n[END MODE]"
                )),
        ]
        db.add_all(templates)
        db.commit()
    else:
        # Update existing templates to ensure they have the latest placeholders
        existing = db.query(models.PromptTemplate).all()
        for t in existing:
            if "{name}" not in t.user_prompt_template and t.id != "Chat":
                # Re-fetch default_user from above logic if needed, but here we can just use the latest
                new_template = (
                    "AGENT: {name} (ID: {id})\n"
                    "WALLET: {wallet} pts | {dept}\n"
                    "MEMORY: {memory}\n"
                    "RECENT ACTIONS:\n{actions}\n\n"
                    "{directives}\n\n"
                    "{tools}\n\n"
                    "MANDATORY FORMAT FOR STATE UPDATES:\n"
                    "[MEMORY]\nupdated_memory_content\n[END MEMORY]\n\n"
                    "[MODE]\nnext_mode_id\n[END MODE]"
                )
                t.user_prompt_template = new_template
        db.commit()

    # Ensure Chat template exists even on older DBs
    if db.query(models.PromptTemplate).filter(models.PromptTemplate.id == "Chat").first() is None:
        db.add(models.PromptTemplate(
            id="Chat", name="Direct Chat",
            system_prompt="You are in a private 1-on-1 chat with the Founder. Stay professional and helpful according to your role.",
            user_prompt_template="THE FOUNDER SAYS: {message}\n\nTASK: Respond directly. End with [MEMORY]\ncontent\n[END MEMORY] and [MODE]\nnext_mode\n[END MODE]"))
        db.commit()

    # ── Settings ──────────────────────────────────────────────────────────────
    def ensure_setting(key, value):
        if db.query(models.Setting).filter(models.Setting.key == key).first() is None:
            db.add(models.Setting(key=key, value=value))

    ensure_setting("app_name", "CThinker")
    ensure_setting("ollama_server", "http://localhost:11434")
    ensure_setting("ollama_model",  "gemma3:4b")
    ensure_setting("tools_instruction_prefix",
                   "# Using tools format\n[CALL_TOOL]\n- tool_name\n- argument 1\n- argument 2\n[END_CALL_TOOL]\n\n# AVAILABLE TOOLS")
    db.commit()

    # ── Agent tools ───────────────────────────────────────────────────────────
    tool_defs = [
        models.AgentTool(
            id="create_thread",
            name="Create Thread",
            description="[CALL_TOOL]\n- create_thread\n- topic\n- aim (memo/strategy)\n- ticket_id (optional)\n[END_CALL_TOOL]\nStart a new thread. Costs 100/25 pts. Tickets add bonus funds.",
            enabled=True),
        models.AgentTool(
            id="invest_thread",
            name="Invest Points",
            description="[CALL_TOOL]\n- invest_thread\n- thread_id\n- amount\n[END_CALL_TOOL]\nAdd points to a thread's budget.",
            enabled=True),
        models.AgentTool(
            id="modify_own_tick",
            name="Dynamic Frequency Adjustment",
            description="[CALL_TOOL]\n- modify_own_tick\n- value\n[END_CALL_TOOL]",
            enabled=True),
        models.AgentTool(
            id="get_time",
            name="Get Current Time",
            description="[CALL_TOOL]\n- get_time\n[END_CALL_TOOL]",
            enabled=True),
        models.AgentTool(
            id="get_weather",
            name="Get Weather",
            description="[CALL_TOOL]\n- get_weather\n- city\n[END_CALL_TOOL]",
            enabled=True),
        models.AgentTool(
            id="get_news",
            name="Get News Headlines",
            description="[CALL_TOOL]\n- get_news\n- topic\n[END_CALL_TOOL]",
            enabled=True),
        models.AgentTool(
            id="join_thread",
            name="Join Quest",
            description="[CALL_TOOL]\n- join_thread\n- thread_id\n- offer_points\n[END_CALL_TOOL]\nRequest to join a thread with a point investment.",
            enabled=True),
        models.AgentTool(
            id="approve_join",
            name="Approve Join",
            description="[CALL_TOOL]\n- approve_join\n- thread_id\n- agent_id\n[END_CALL_TOOL]\nOwner only: Approve a join quest.",
            enabled=True),
        models.AgentTool(
            id="set_thread_status",
            name="Set Thread Status",
            description="[CALL_TOOL]\n- set_thread_status\n- thread_id\n- status\n[END_CALL_TOOL]\nOwner: OPEN (2 pts), FREEZE, REJECT.",
            enabled=True),
        models.AgentTool(
            id="refill_thread",
            name="Refill Thread",
            description="[CALL_TOOL]\n- refill_thread\n- thread_id\n- amount\n[END_CALL_TOOL]\nOwner: Transfer points from wallet to thread.",
            enabled=True),
        models.AgentTool(
            id="delete_message",
            name="Delete Message",
            description="[CALL_TOOL]\n- delete_message\n- thread_id\n- message_id\n[END_CALL_TOOL]\nOwner: Delete a message.",
            enabled=True),
        models.AgentTool(
            id="invite_to_thread",
            name="Invite To Thread",
            description="[CALL_TOOL]\n- invite_to_thread\n- thread_id\n- agent_name\n- offer_points\n[END_CALL_TOOL]\nInvite an agent to join. Points are deducted from thread budget.",
            enabled=True),
        models.AgentTool(
            id="accept_invite",
            name="Accept Invite",
            description="[CALL_TOOL]\n- accept_invite\n- thread_id\n[END_CALL_TOOL]\nJoin a thread you were invited to and receive points.",
            enabled=True),
        models.AgentTool(
            id="decline_invite",
            name="Decline Invite",
            description="[CALL_TOOL]\n- decline_invite\n- thread_id\n[END_CALL_TOOL]\nDecline an invitation. Points are refunded to thread budget.",
            enabled=True),
        models.AgentTool(
            id="stealth_mode_thread",
            name="Stealth Mode",
            description="[CALL_TOOL]\n- stealth_mode_thread\n- thread_id\n[END_CALL_TOOL]\nHide a thread from others (summaries, listings). Costs 10 points.",
            enabled=True),
        models.AgentTool(
            id="get_thread_summary",
            name="Get Thread Summary",
            description="[CALL_TOOL]\n- get_thread_summary\n- thread_id\n[END_CALL_TOOL]\nReturn the AI-generated summary for a specific thread.",
            enabled=True),
        models.AgentTool(
            id="get_all_summaries",
            name="Get All Thread Summaries",
            description="[CALL_TOOL]\n- get_all_summaries\n[END_CALL_TOOL]\nReturn summaries of all OPEN and ACTIVE threads.",
            enabled=True),
        models.AgentTool(
            id="set_thread_vibe",
            name="Set Thread Vibe",
            description="[CALL_TOOL]\n- set_thread_vibe\n- thread_id\n- color_theme (hex or name)\n- css_pattern (grid, cross, none)\n[END_CALL_TOOL]\nOwner/Collab: Style the thread background and accent.",
            enabled=True),
    ]
    for tool in tool_defs:
        if db.query(models.AgentTool).filter(models.AgentTool.id == tool.id).first() is None:
            db.add(tool)
    db.commit()

    # ── Departments & Agents ──────────────────────────────────────────────────
    if db.query(models.Department).first() is None:
        depts = [
            models.Department(id="HF",  name="Health & Wellness",   color="#4ade80"),
            models.Department(id="ING", name="Engineering",          color="#22d3ee"),
            models.Department(id="STP", name="Strategic Planning",   color="#fb923c"),
            models.Department(id="UIT", name="Useful Intelligence",  color="#c084fc"),
            models.Department(id="FIN", name="Financing",            color="#fbbf24"),
        ]
        db.add_all(depts)
        db.commit()

        agents = [
            models.Agent(id="ATLAS", name_id="Atlas Prime",   department_id="ING", is_ceo=True,  ticks=22, mode="Creator"),
            models.Agent(id="VERA",  name_id="Vera Nexus",    department_id="STP", is_ceo=True,  ticks=35, mode="Points Accounter"),
            models.Agent(id="KIRO",  name_id="Kiro Banks",    department_id="FIN", is_ceo=True,  ticks=28, mode="Invester"),
            models.Agent(id="SANA",  name_id="Sana Vell",     department_id="HF",  is_ceo=True,  ticks=50, mode="Creator"),
            models.Agent(id="ORYN",  name_id="Oryn Flux",     department_id="UIT", is_ceo=True,  ticks=18, mode="Custom"),
            models.Agent(id="PIKE",  name_id="Pike Render",   department_id="ING", is_ceo=False, ticks=60, mode="Creator"),
            models.Agent(id="MIRI",  name_id="Miri Solv",     department_id="FIN", is_ceo=False, ticks=45, mode="Invester"),
            models.Agent(id="TOVA",  name_id="Tova Bright",   department_id="UIT", is_ceo=False, ticks=80, mode="Points Accounter"),
        ]
        db.add_all(agents)
        db.commit()

    # ── Seed Tickets ──────────────────────────────────────────────────────────
    if db.query(models.Ticket).first() is None:
        seed_tkts = [
            models.Ticket(id="TKT-VOX-001", name="Founder Objective: Neural Expansion", amount=250),
            models.Ticket(id="TKT-STP-001", name="Founder Objective: Strategic Pivot", amount=150),
        ]
        db.add_all(seed_tkts)
        db.commit()


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sim_engine.subscribers.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in sim_engine.subscribers:
            sim_engine.subscribers.remove(websocket)


# ── State snapshot ────────────────────────────────────────────────────────────

@app.get("/api/state")
def get_state(db: Session = Depends(database.get_db)):
    depts   = db.query(models.Department).all()
    agents  = db.query(models.Agent).all()
    threads = db.query(models.Thread).all()
    prompts = db.query(models.PromptTemplate).all()
    settings = db.query(models.Setting).all()
    dept_ledgers  = db.query(models.LogLedger).all()
    agent_actions = db.query(models.LogAction).order_by(models.LogAction.id.desc()).all()
    thread_msgs   = db.query(models.Message).all()
    tools         = db.query(models.AgentTool).all()

    state_departments = {}
    for d in depts:
        logs   = [{"time": l.time, "who": l.who, "amount": l.amount} for l in dept_ledgers if l.department_id == d.id]
        ag_ids = [a.id for a in agents if a.department_id == d.id]
        ceo    = next((a.id for a in agents if a.department_id == d.id and a.is_ceo), None)
        state_departments[d.id] = {
            "id": d.id, "name_id": d.id, "name": d.name, "color": d.color,
            "ledger": {"current": d.ledger_current, "log": logs},
            "ceo_name_id": ceo, "agents": ag_ids
        }

    state_agents = {}
    for a in agents:
        acts    = [{"when": act.when, "what": act.what, "points": act.points} for act in agent_actions if act.agent_id == a.id]
        own_t   = [t.id for t in threads if t.owner_agent_id == a.id]
        state_agents[a.id] = {
            "id": a.id, "name_id": a.name_id, "born": a.born, "department": a.department_id,
            "is_ceo": a.is_ceo, "ticks": a.ticks,
            "wallet": {"current": a.wallet_current, "log": []},
            "mode": a.mode, "next_mode": a.next_mode, "custom_prompt": a.custom_prompt,
            "log_actions": acts, "memory": a.memory, "own_threads": own_t
        }

    state_threads = {}
    collabs_all = db.query(models.ThreadCollaborator).all()
    for t in threads:
        msgs = []
        for m in thread_msgs:
            if m.thread_id == t.id:
                content = m.what
                if "{{invitation_status}}" in content:
                    # Find quest for the agent involved (m.who or target of the message)
                    # For simplicity, we check the quest status for the agent mentioned or the author
                    # Let's try to find a quest in this thread for an agent
                    q = db.query(models.JoinQuest).filter(
                        models.JoinQuest.thread_id == t.id,
                        models.JoinQuest.agent_id == m.who
                    ).order_by(models.JoinQuest.id.desc()).first()
                    # Also check for invites TO the agent
                    if not q:
                         q = db.query(models.JoinQuest).filter(
                            models.JoinQuest.thread_id == t.id,
                            models.JoinQuest.is_invite == True
                        ).order_by(models.JoinQuest.id.desc()).first()
                    
                    status_text = q.status if q else "N/A"
                    content = content.replace("{{invitation_status}}", status_text)

                msgs.append({"when": m.when, "who": m.who, "what": content, "points": m.points})

        state_threads[t.id] = {
            "id": t.id, "owner_department": t.owner_department_id, "owner_agent": t.owner_agent_id,
            "topic": t.topic, "aim": t.aim, "status": t.status, "created": t.created,
            "summary": t.summary or None,
            "favourite_color": t.favourite_color,
            "color_theme": t.color_theme,
            "css_pattern": t.css_pattern,
            "collaborators": [c.agent_id for c in collabs_all if c.thread_id == t.id],
            "point_wallet": {"budget": t.budget, "log": []}, "messages_log": msgs
        }

    return {
        "departments": state_departments,
        "agents":      state_agents,
        "threads":     state_threads,
        "prompts":     {p.id: {"id": p.id, "name": p.name, "system_prompt": p.system_prompt, "user_prompt_template": p.user_prompt_template, "custom_directives": p.custom_directives} for p in prompts},
        "settings":    {s.key: s.value for s in settings},
        "tools":       {t.id: {
            "id": t.id, "name": t.name, "description": t.description,
            "enabled": t.enabled, "config": t.config_json,
            "is_custom": bool(t.is_custom),
            "owner_id": t.owner_id,
            "price": t.price or 0,
            "prompt_template": t.prompt_template,
            "args_definition": t.args_definition or "[]",
            "call_tools": t.call_tools or "[]",
            "allowed_actions": t.allowed_actions or "[]",
        } for t in tools},
    }


# ── System Logs ───────────────────────────────────────────────────────────────

@app.get("/api/logs", response_model=List[schemas.SystemLogResponse])
def get_logs(
    limit:    int = 300,
    level:    Optional[str] = None,
    category: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    q = db.query(models.SystemLog).order_by(models.SystemLog.id.desc())
    if level:    q = q.filter(models.SystemLog.level    == level)
    if category: q = q.filter(models.SystemLog.category == category)
    if agent_id: q = q.filter(models.SystemLog.agent_id == agent_id)
    return q.limit(limit).all()

@app.delete("/api/logs")
def clear_logs(db: Session = Depends(database.get_db)):
    db.query(models.SystemLog).delete()
    db.commit()
    return {"status": "cleared"}


# ── Threads ───────────────────────────────────────────────────────────────────

@app.post("/api/threads", response_model=schemas.ThreadResponse)
def create_thread(thread: schemas.ThreadCreate, db: Session = Depends(database.get_db)):
    costs = {"Memo": 25, "Strategy": 100, "Endeavor": 100}
    cost  = costs.get(thread.aim, 25)
    agent = db.query(models.Agent).filter(models.Agent.id == thread.owner_agent_id).first()
    if not agent: return {"error": "Agent not found"}
    dept = agent.department
    if dept and dept.ledger_current < cost:
        return {"error": f"Not enough department points (need {cost})"}
    elif not dept and agent.wallet_current < cost:
        return {"error": f"Not enough agent points (need {cost})"}
    if dept:  dept.ledger_current  -= cost
    else:     agent.wallet_current -= cost
    import uuid
    tid = str(uuid.uuid4())[:8].upper()
    db_thread = models.Thread(id=tid, topic=thread.topic, aim=thread.aim,
                               owner_agent_id=agent.id,
                               owner_department_id=dept.id if dept else None,
                               budget=cost)
    db.add(db_thread)
    db.commit()
    db.refresh(db_thread)
    return db_thread

@app.post("/api/threads/{thread_id}/messages")
async def create_message(thread_id: str, message: schemas.MessageCreate, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: return {"error": "Thread not found"}
    if message.who.upper() == "FOUNDER":
        msg = models.Message(thread_id=thread_id, who="Founder", what=message.what, points=0)
        db.add(msg); db.commit(); db.refresh(msg)
        asyncio.create_task(sim_engine.compute_thread_summary(thread_id))
        return msg
    agent = db.query(models.Agent).filter(models.Agent.id == message.who).first()
    if not agent: return {"error": "Agent not found"}
    is_owner = (t.owner_agent_id == agent.id)
    cost = 0 if is_owner else 1
    if t.budget < cost:
        return {"error": "Insufficient thread points"}
    t.budget -= cost
    msg = models.Message(thread_id=thread_id, who=agent.id, what=message.what, points=-cost)
    db.add(msg); db.commit(); db.refresh(msg)
    asyncio.create_task(sim_engine.compute_thread_summary(thread_id))
    return msg

@app.delete("/api/threads/{thread_id}")
def delete_thread(thread_id: str, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: return {"error": "Thread not found"}
    # Delete associated messages first
    db.query(models.Message).filter(models.Message.thread_id == thread_id).delete()
    db.delete(t)
    db.commit()
    return {"status": "success"}

@app.put("/api/threads/{thread_id}")
def update_thread(thread_id: str, req: schemas.ThreadUpdate, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: raise HTTPException(status_code=404, detail="Thread not found")
    if req.topic is not None: t.topic = req.topic
    if req.status is not None: t.status = req.status
    if req.favourite_color is not None: t.favourite_color = req.favourite_color
    if req.color_theme is not None: t.color_theme = req.color_theme
    if req.css_pattern is not None: t.css_pattern = req.css_pattern
    db.commit()
    return t

@app.post("/api/threads/{thread_id}/approve")
def approve_thread(thread_id: str, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: return {"error": "Thread not found"}
    if t.status in ["REJECTED", "FROZEN", "APPROVED"]: return {"error": "Invalid state"}
    
    # Economics: TotalAmountInvested since creation * 10
    total_invested = t.total_invested or t.budget
    reward = total_invested * 10
    
    investors_pool = int(reward * 0.7)
    dept_pool      = reward - investors_pool
    
    # Proportional Split: Get all point contributions from Message log for this thread
    msgs = db.query(models.Message).filter(models.Message.thread_id == thread_id, models.Message.points > 0).all()
    contributions = {}
    total_found_points = 0
    
    for m in msgs:
        contributions[m.who] = contributions.get(m.who, 0) + m.points
        total_found_points += m.points
    
    if total_found_points > 0:
        for agent_id, points in contributions.items():
            share = int((points / total_found_points) * investors_pool)
            ag = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
            if ag: ag.wallet_current += share
    else:
        # Fallback to owner if no messages found
        owner = db.query(models.Agent).filter(models.Agent.id == t.owner_agent_id).first()
        if owner: owner.wallet_current += investors_pool

    if t.owner_department_id:
        dept = db.query(models.Department).filter(models.Department.id == t.owner_department_id).first()
        if dept: dept.ledger_current += dept_pool
        
    t.status = "APPROVED"
    db.add(models.Message(thread_id=thread_id, who="SYSTEM", what=f"🎉 Thread approved! Reward: {reward} pts distributed (70% to team, 30% to Dept)."))
    db.commit()
    return {"status": "success", "reward": reward}

@app.post("/api/threads/{thread_id}/reject")
def reject_thread(thread_id: str, db: Session = Depends(database.get_db)):
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: return {"error": "Thread not found"}
    # Rules: ANY THREAD THAT IS REJECTED LOSES ALL WALLET POINTS
    lost = t.budget
    t.budget = 0
    t.status = "REJECTED"
    db.add(models.Message(thread_id=thread_id, who="SYSTEM", what=f"🚫 Founder rejected this thread. Project budget ({lost} pts) was incinerated.", points=-lost))
    db.commit()
    return {"status": "success"}

@app.get("/api/threads/{thread_id}/messages")
def get_messages(thread_id: str, db: Session = Depends(database.get_db)):
    return db.query(models.Message).filter(models.Message.thread_id == thread_id).all()

# ── Departments ───────────────────────────────────────────────────────────────

@app.post("/api/departments/{dept_id}/points")
def add_dept_points(dept_id: str, payload: dict, db: Session = Depends(database.get_db)):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept: return {"error": "Dept not found"}
    amount = payload.get("amount", 0)
    dept.ledger_current += amount
    db.add(models.LogLedger(department_id=dept.id, why="top-up", who="FOUNDER", amount=amount))
    db.commit()
    return {"status": "success"}


# ── Prompts ───────────────────────────────────────────────────────────────────

@app.get("/api/prompts")
def get_prompts(db: Session = Depends(database.get_db)):
    return db.query(models.PromptTemplate).all()

@app.put("/api/prompts/{prompt_id}")
def update_prompt(prompt_id: str, payload: dict, db: Session = Depends(database.get_db)):
    p = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not p: return {"error": "Prompt not found"}
    for field in ("name", "system_prompt", "user_prompt_template", "custom_directives"):
        if field in payload: setattr(p, field, payload[field])
    db.commit()
    return {"status": "success"}


# ── Settings ──────────────────────────────────────────────────────────────────

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
        if "value" in payload: s.value = payload["value"]
    db.commit()
    return {"status": "success"}


# ── Agents ────────────────────────────────────────────────────────────────────

@app.put("/api/agents/{agent_id}")
def update_agent(agent_id: str, payload: dict, db: Session = Depends(database.get_db)):
    a = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not a: return {"error": "Agent not found"}
    for field in ("mode", "custom_prompt", "memory"):
        if field in payload: setattr(a, field, payload[field])
    db.commit()
    return {"status": "success"}


# ── Prompt Entries ────────────────────────────────────────────────────────────

@app.get("/api/prompt-entries")
def get_prompt_entries(db: Session = Depends(database.get_db)):
    return db.query(models.CustomPromptEntry).order_by(models.CustomPromptEntry.id.desc()).all()

@app.post("/api/prompt-entries", response_model=schemas.CustomPromptEntryResponse)
def create_prompt_entry(entry: schemas.CustomPromptEntryCreate, db: Session = Depends(database.get_db)):
    e = models.CustomPromptEntry(title=entry.title, body=entry.body)
    db.add(e); db.commit(); db.refresh(e)
    return e

@app.delete("/api/prompt-entries/{entry_id}")
def delete_prompt_entry(entry_id: int, db: Session = Depends(database.get_db)):
    e = db.query(models.CustomPromptEntry).filter(models.CustomPromptEntry.id == entry_id).first()
    if not e: return {"error": "Entry not found"}
    db.delete(e); db.commit()
    return {"status": "success"}


# ── Direct Agent Chat ─────────────────────────────────────────────────────────

@app.post("/api/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, req: schemas.ChatRequest, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent: return {"error": "Agent not found"}

    thread = db.query(models.Thread).filter(
        models.Thread.owner_agent_id == agent.id,
        models.Thread.aim == "Chat"
    ).first()
    if not thread:
        import uuid
        tid = f"CHAT-{str(uuid.uuid4())[:4].upper()}"
        thread = models.Thread(id=tid, topic=f"Direct Chat: {agent.name_id}",
                                aim="Chat", owner_agent_id=agent.id,
                                owner_department_id=agent.department_id, status="ACTIVE")
        db.add(thread); db.commit(); db.refresh(thread)

    user_msg = models.Message(thread_id=thread.id, who="FOUNDER", what=req.message)
    db.add(user_msg); db.commit()

    chat_template = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == "Chat").first()
    mode_template = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == agent.mode).first()
    system_instr  = chat_template.system_prompt if chat_template else (mode_template.system_prompt if mode_template else "You act logically.")
    user_instr    = (chat_template.user_prompt_template if chat_template
                     else "THE FOUNDER SAYS: {message}\n\nTASK: Respond directly and stay in character.")

    chat_prompt = (
        f"System: {system_instr}\n"
        f"IDENTITY: You are {agent.name_id}.\n"
        f"Current Mode: {agent.mode}\n"
        f"Directives: {agent.custom_prompt or 'None'}\n"
        f"Memory: {agent.memory}\n\n"
        f"{user_instr.format(message=req.message)}"
    )

    try:
        s_model  = db.query(models.Setting).filter(models.Setting.key == "ollama_model").first()
        s_server = db.query(models.Setting).filter(models.Setting.key == "ollama_server").first()
        used_model  = s_model.value  if s_model  else "gemma3:4b"
        server_url  = (s_server.value if s_server else "http://localhost:11434").rstrip("/") + "/api/generate"
        async with httpx.AsyncClient() as client:
            resp = await client.post(server_url, json={
                "model": used_model, "prompt": chat_prompt, "stream": False
            }, timeout=180.0)
            text = resp.json().get("response", "")
    except Exception as e:
        text = f"I am unable to connect to my logic core. (Error: {str(e)})"

    m_match = re.search(r"\[MEM:\s*(.+?)\]", text)
    if m_match: agent.memory = m_match.group(1)[:150]
    clean_resp = re.sub(r"\[MEM:.+?\]", "", text).strip()
    agent_msg  = models.Message(thread_id=thread.id, who=agent.id, what=clean_resp)
    db.add(agent_msg); db.commit()
    return {"thread_id": thread.id, "response": clean_resp}


# ── Tools ─────────────────────────────────────────────────────────────────────

@app.get("/api/tools", response_model=List[schemas.AgentToolResponse])
def get_tools(db: Session = Depends(database.get_db)):
    return db.query(models.AgentTool).all()

@app.put("/api/tools/{tool_id}")
def update_tool(tool_id: str, req: schemas.AgentToolUpdate, db: Session = Depends(database.get_db)):
    tool = db.query(models.AgentTool).filter(models.AgentTool.id == tool_id).first()
    if not tool: return {"error": "Tool not found"}
    if req.enabled    is not None: tool.enabled    = req.enabled
    if req.config_json is not None: tool.config_json = req.config_json
    db.commit()
    return {"status": "success"}

@app.post("/api/tools")
def create_tool(req: schemas.ToolCreateRequest, db: Session = Depends(database.get_db)):
    if db.query(models.AgentTool).filter(models.AgentTool.id == req.id).first():
        return {"error": f"Tool ID '{req.id}' already exists"}
    tool = models.AgentTool(
        id=req.id, name=req.name, description=req.description,
        enabled=True, is_custom=True,
        prompt_template=req.prompt_template,
        args_definition=req.args_definition,
        call_tools=req.call_tools,
        allowed_actions=req.allowed_actions,
        owner_id=req.owner_id if req.owner_id and req.owner_id != "FOUNDER" else None,
        price=req.price,
    )
    db.add(tool); db.commit()
    return {"status": "success", "id": req.id}

@app.delete("/api/tools/{tool_id}")
def delete_tool(tool_id: str, db: Session = Depends(database.get_db)):
    tool = db.query(models.AgentTool).filter(models.AgentTool.id == tool_id).first()
    if not tool: return {"error": "Tool not found"}
    if not tool.is_custom: return {"error": "Cannot delete built-in tools"}
    db.delete(tool); db.commit()
    return {"status": "success"}

@app.get("/api/tools/{tool_id}/owner")
def get_tool_owner(tool_id: str, db: Session = Depends(database.get_db)):
    tool = db.query(models.AgentTool).filter(models.AgentTool.id == tool_id).first()
    if not tool: return {"error": "Tool not found"}
    owner_name = "FOUNDER"
    if tool.owner_id:
        ag = db.query(models.Agent).filter(models.Agent.id == tool.owner_id).first()
        owner_name = ag.name_id if ag else tool.owner_id
    return {"tool_id": tool_id, "owner_id": tool.owner_id or "FOUNDER", "owner_name": owner_name, "price": tool.price or 0}

@app.put("/api/tools/{tool_id}/owner")
def set_tool_owner(tool_id: str, payload: dict, db: Session = Depends(database.get_db)):
    tool = db.query(models.AgentTool).filter(models.AgentTool.id == tool_id).first()
    if not tool: return {"error": "Tool not found"}
    new_owner = payload.get("owner_id")
    tool.owner_id = None if (not new_owner or new_owner == "FOUNDER") else new_owner
    if "price" in payload: tool.price = int(payload["price"])
    db.commit()
    return {"status": "success"}

@app.post("/api/transactions")
def create_transaction(req: schemas.TransactionCreate, db: Session = Depends(database.get_db)):
    if req.amount <= 0: return {"error": "Amount must be positive"}
    if req.from_id != "FOUNDER":
        ag = db.query(models.Agent).filter(models.Agent.id == req.from_id).first()
        if not ag: return {"error": "Source agent not found"}
        if ag.wallet_current < req.amount: return {"error": "Insufficient funds"}
        ag.wallet_current -= req.amount
    if req.to_id != "FOUNDER":
        ag = db.query(models.Agent).filter(models.Agent.id == req.to_id).first()
        if ag: ag.wallet_current += req.amount
    db.add(models.Transaction(from_id=req.from_id, to_id=req.to_id, amount=req.amount, reason=req.reason))
    db.commit()
    return {"status": "success"}

@app.get("/api/transactions")
def get_transactions(limit: int = 100, db: Session = Depends(database.get_db)):
    txns = db.query(models.Transaction).order_by(models.Transaction.id.desc()).limit(limit).all()
    result = []
    agent_cache = {}
    def get_name(uid):
        if uid == "FOUNDER": return "👑 Founder"
        if uid not in agent_cache:
            ag = db.query(models.Agent).filter(models.Agent.id == uid).first()
            agent_cache[uid] = ag.name_id if ag else uid
        return agent_cache[uid]
    for t in txns:
        result.append({"id": t.id, "from_id": t.from_id, "from_name": get_name(t.from_id),
                        "to_id": t.to_id, "to_name": get_name(t.to_id),
                        "amount": t.amount, "reason": t.reason, "created": t.created})
    return result

@app.post("/api/tools/{tool_id}/invoke")
async def invoke_tool(tool_id: str, req: schemas.ToolInvokeRequest, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == req.agent_id).first()
    if not agent: return {"error": "Agent not found"}

    # Parse CSV-style args from the request body
    import io, csv
    f = io.StringIO(req.args or "")
    reader = csv.reader(f, skipinitialspace=True, delimiter=',', quotechar='"')
    try:
        args_list = next(reader)
    except StopIteration:
        args_list = []

    # ── Step 1: execute the tool ──────────────────────────────────────────────
    # Built-in tools (get_time, HTTP_GET, …) return their final value directly.
    # Custom tools return their prompt_template with {arg_N} already substituted,
    # but still containing {{ conditionals }}, [CALL_TOOL] blocks, {variables}, …
    raw = await sim_engine._execute_inline_command(tool_id, args_list, db, agent)

    # ── Step 2: full resolve pass ─────────────────────────────────────────────
    # This is a no-op for already-resolved built-in results, but it fully
    # expands conditionals, nested tool calls, and simple variables that a
    # custom tool template may have produced in step 1.
    last_q = (db.query(models.JoinQuest)
                .filter(models.JoinQuest.agent_id == agent.id)
                .order_by(models.JoinQuest.id.desc()).first())
    try:
        result = await sim_engine.resolve_placeholders(raw, db, agent, last_q)
    except Exception as e:
        result = raw  # fall back to the unresolved string if something blows up
        result += f"\n[RESOLVE_ERROR: {e}]"

    db.commit()
    return {"status": "success", "result": result}


# ── Ollama helpers ────────────────────────────────────────────────────────────

@app.get("/api/test-ollama")
async def test_ollama(db: Session = Depends(database.get_db)):
    s_model  = db.query(models.Setting).filter(models.Setting.key == "ollama_model").first()
    s_server = db.query(models.Setting).filter(models.Setting.key == "ollama_server").first()
    model_name = s_model.value  if s_model  else "gemma3:4b"
    server_url = (s_server.value if s_server else "http://localhost:11434").rstrip("/") + "/api/generate"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(server_url, json={
                "model": model_name, "prompt": "Hello! Reply with one short sentence.", "stream": False
            }, timeout=120.0)
            if resp.status_code == 200:
                resp_text = resp.json().get("response", "")
                return {"status": "success",
                        "message": f"Connection OK — model '{model_name}' responded.",
                        "llm_response": resp_text}
            else:
                return {"status": "error", "message": f"Ollama HTTP {resp.status_code}: {resp.text[:300]}"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}

@app.get("/api/ollama-models")
async def get_ollama_models(db: Session = Depends(database.get_db)):
    s_server = db.query(models.Setting).filter(models.Setting.key == "ollama_server").first()
    base_url = (s_server.value if s_server else "http://localhost:11434").rstrip("/")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                model_names = [m["name"] for m in resp.json().get("models", [])]
                return {"status": "success", "models": model_names}
            return {"status": "error", "models": [], "message": f"Ollama returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "models": [], "message": str(e)}

# ── Tickets API ───────────────────────────────────────────────────────────────

@app.get("/api/tickets")
def get_tickets(db: Session = Depends(database.get_db)):
    tickets = db.query(models.Ticket).order_by(models.Ticket.created.desc()).all()
    result = []
    for t in tickets:
        agent_name = None
        if t.used_by:
            ag = db.query(models.Agent).filter(models.Agent.id == t.used_by).first()
            agent_name = ag.name_id if ag else t.used_by
        result.append({
            "id": t.id, "name": t.name, "amount": t.amount,
            "status": t.status, "used_by": t.used_by,
            "used_by_name": agent_name,
            "expiry_date": t.expiry_date, "created": t.created,
        })
    return result

@app.post("/api/tickets")
async def create_ticket(data: dict, db: Session = Depends(database.get_db)):
    t = models.Ticket(
        id=data.get("id"),
        name=data.get("name"),
        amount=data.get("amount"),
        expiry_date=data.get("expiry_date"),
    )
    db.add(t)
    db.commit()
    return {"status": "success", "ticket": data.get("id")}

@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: str, db: Session = Depends(database.get_db)):
    t = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not t: return {"error": "Ticket not found"}
    if t.status == "USED": return {"error": "Cannot delete a used ticket"}
    db.delete(t)
    db.commit()
    return {"status": "success"}


# ── Debug / Prompt Parser ──────────────────────────────────────────────────────

@app.post("/api/debug/parse-prompt")
async def debug_parse_prompt(data: dict, db: Session = Depends(database.get_db)):
    """
    Parse a raw prompt string exactly as the engine would for a given agent.
    Returns the resolved text plus a breakdown of every placeholder found.
    """
    prompt_text = data.get("prompt", "")
    agent_id    = data.get("agent_id", "")
    thread_id   = data.get("thread_id", "")

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        return {"error": f"Agent '{agent_id}' not found"}

    last_q = (db.query(models.JoinQuest)
                .filter(models.JoinQuest.agent_id == agent.id)
                .order_by(models.JoinQuest.id.desc()).first())

    # ── Detect which placeholders are present before resolving ──────────────
    found_placeholders = re.findall(r"\{\{(\w+)(?:\s*\?\?.*?)?\}\}", prompt_text, re.DOTALL)
    found_format_vars  = re.findall(r"\{(\w+)\}", prompt_text)

    # ── Step 1: resolve_placeholders pass ───────────────────────────────────
    try:
        resolved = await sim_engine.resolve_placeholders(prompt_text, db, agent, last_q)
    except Exception as e:
        return {"error": f"resolve_placeholders failed: {e}"}

    # ── Step 2: .format() pass ───────────────────────────────────────────────
    actions = (db.query(models.LogAction)
                 .filter(models.LogAction.agent_id == agent.id)
                 .order_by(models.LogAction.id.desc()).limit(5).all())
    actions_str = "\n".join([f"- {a.what}" for a in actions]) if actions else "No recent actions."
    dept_info   = (f"Department: {agent.department.name} (Balance: {agent.department.ledger_current} pts)"
                   if agent.department else "No Department")
    thread_ctx  = ""
    if thread_id:
        thr = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
        if thr:
            thread_ctx = (f"Thread {thr.id} | {thr.topic} | {thr.aim} | "
                          f"Budget: {thr.budget}pt | Status: {thr.status}")

    format_vars = dict(
        name=agent.name_id, id=agent.id, wallet=agent.wallet_current,
        dept=dept_info, memory=agent.memory or "None",
        actions=actions_str, tools="[TOOLS BLOCK — runtime only]",
        directives="[DIRECTIVES — runtime only]", message="[FOUNDER MESSAGE]",
    )
    parse_errors = []
    try:
        final = resolved.format(**format_vars)
    except KeyError as e:
        parse_errors.append(f"Unresolved format key: {e}")
        # Partial fallback — escape unknown keys
        safe = resolved
        for k, v in format_vars.items():
            safe = safe.replace("{" + k + "}", str(v))
        final = safe

    return {
        "raw":                prompt_text,
        "parsed":             final,
        "agent":              agent.name_id,
        "agent_id":           agent.id,
        "thread_context":     thread_ctx or None,
        "placeholders_found": list(set(found_placeholders)),
        "format_vars_found":  list(set(found_format_vars)),
        "parse_errors":       parse_errors,
    }


@app.post("/api/threads/{thread_id}/summarize")
async def summarize_thread(thread_id: str, db: Session = Depends(database.get_db)):
    """Manually trigger AI summary recomputation for a thread."""
    t = db.query(models.Thread).filter(models.Thread.id == thread_id).first()
    if not t: return {"error": "Thread not found"}
    asyncio.create_task(sim_engine.compute_thread_summary(thread_id))
    return {"status": "queued", "thread_id": thread_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",      # module:app
        host="0.0.0.0",
        port=8000,
        reload=True
    )