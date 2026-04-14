from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from database import Base

def get_stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class Department(Base):
    __tablename__ = "departments"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    color = Column(String)
    ledger_current = Column(Integer, default=500)
    
    agents = relationship("Agent", back_populates="department")
    threads = relationship("Thread", back_populates="owner_department")

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    system_prompt = Column(Text)
    user_prompt_template = Column(Text, nullable=True)
    custom_directives = Column(Text, nullable=True)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

class CustomPromptEntry(Base):
    __tablename__ = "custom_prompt_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created = Column(String, default=get_stamp)

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, index=True)
    name_id = Column(String)
    born = Column(String, default=get_stamp)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    is_ceo = Column(Boolean, default=False)
    ticks = Column(Integer, default=60)
    wallet_current = Column(Integer, default=50)
    mode = Column(String, ForeignKey("prompt_templates.id"), default="Points Accounter")
    next_mode = Column(String, ForeignKey("prompt_templates.id"), nullable=True)
    custom_prompt = Column(Text, default="")
    memory = Column(String, default="")
    
    department = relationship("Department", back_populates="agents")

class Thread(Base):
    __tablename__ = "threads"
    id = Column(String, primary_key=True, index=True)
    owner_department_id = Column(String, ForeignKey("departments.id"))
    owner_agent_id = Column(String, ForeignKey("agents.id"))
    topic = Column(String)
    aim = Column(String)
    status = Column(String, default="OPEN")
    created = Column(String, default=get_stamp)
    budget = Column(Integer, default=0)
    total_invested = Column(Integer, default=0)
    last_tax_check = Column(String, default=get_stamp)
    ticket_id = Column(String, nullable=True)
    ticket_value = Column(Integer, default=0)
    summary = Column(Text, nullable=True)       # AI-generated summary, recomputed on new messages
    is_stealth = Column(Boolean, default=False)
    favourite_color = Column(String, nullable=True)
    color_theme = Column(String, nullable=True)
    css_pattern = Column(String, nullable=True)
    
    owner_department = relationship("Department", back_populates="threads")
    collaborators = relationship("ThreadCollaborator", back_populates="thread")

class ThreadCollaborator(Base):
    __tablename__ = "thread_collaborators"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String, ForeignKey("threads.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    joined_at = Column(String, default=get_stamp)
    
    thread = relationship("Thread", back_populates="collaborators")

class JoinQuest(Base):
    __tablename__ = "join_quests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String, ForeignKey("threads.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    offer_points = Column(Integer, default=0)
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    is_invite = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    expires_at = Column(String, nullable=True)
    created = Column(String, default=get_stamp)
    
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String, ForeignKey("threads.id"))
    who = Column(String)
    what = Column(Text)
    when = Column(String, default=get_stamp)
    points = Column(Integer, default=0)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True) # mnemonic like TKT-123
    name = Column(String)
    amount = Column(Integer)
    status = Column(String, default="UNUSED") # UNUSED, USED
    used_by = Column(String, ForeignKey("agents.id"), nullable=True)
    expiry_date = Column(String, nullable=True)   # ISO date string, optional
    created = Column(String, default=get_stamp)

class LogAction(Base):
    __tablename__ = "log_actions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    when = Column(String, default=get_stamp)
    what = Column(Text)
    points = Column(Integer, nullable=True)

class LogLedger(Base):
    __tablename__ = "log_ledger"
    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(String, ForeignKey("departments.id"))
    time = Column(String, default=get_stamp)
    who = Column(String)
    why = Column(String)
    amount = Column(Integer)

class AgentTool(Base):
    __tablename__ = "agent_tools"
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)          # shown to agents in their prompt
    enabled = Column(Boolean, default=True)
    config_json = Column(Text, default="{}")
    # ── Programmatic tool fields ──────────────────────────────────────────────
    is_custom = Column(Boolean, default=False)
    owner_id = Column(String, nullable=True)    # "FOUNDER" or agent ID
    price = Column(Integer, default=0)          # pts charged to non-owners per use
    prompt_template = Column(Text, nullable=True)
    args_definition = Column(Text, default="[]")   # JSON [{name, description}, ...]
    call_tools = Column(Text, default="[]")         # JSON [tool_id, ...]
    allowed_actions = Column(Text, default="[]")    # JSON ["http_get","create_file",...]

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_id = Column(String)      # agent ID or "FOUNDER"
    to_id = Column(String)        # agent ID or "FOUNDER"
    amount = Column(Integer)
    reason = Column(String)
    created = Column(String, default=get_stamp)

# ── System Logger ─────────────────────────────────────────────────────────────
# Stores every meaningful engine event: ticks, LLM calls, tool use, points, errors.
# Level  : INFO | TICK | LLM | TOOL | POINT | WARN | ERROR
# Category: ENGINE | AGENT | LLM | TOOL | SYSTEM
class SystemLog(Base):
    __tablename__ = "system_logs"
    id       = Column(Integer, primary_key=True, autoincrement=True)
    time     = Column(String, default=get_stamp, index=True)
    level    = Column(String, default="INFO")
    category = Column(String, default="ENGINE")
    agent_id = Column(String, nullable=True, index=True)
    dept_id  = Column(String, nullable=True)
    event    = Column(String)
    details  = Column(Text, default="{}")
