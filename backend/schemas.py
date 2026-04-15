from pydantic import BaseModel
from typing import List, Optional

class ThreadBase(BaseModel):
    topic: str
    aim: str
    favourite_color: Optional[str] = None
    color_theme: Optional[str] = None
    css_pattern: Optional[str] = None

class PromptTemplateBase(BaseModel):
    name: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None
    custom_directives: Optional[str] = None

class PromptTemplateResponse(PromptTemplateBase):
    id: str
    class Config:
        from_attributes = True

class SettingBase(BaseModel):
    value: str

class SettingResponse(SettingBase):
    key: str
    class Config:
        from_attributes = True

class ThreadCreate(ThreadBase):
    owner_agent_id: str
    ticket_id: Optional[str] = None

class ThreadUpdate(BaseModel):
    topic: Optional[str] = None
    status: Optional[str] = None
    thread_goal: Optional[str] = None
    current_milestone: Optional[str] = None
    favourite_color: Optional[str] = None
    color_theme: Optional[str] = None
    css_pattern: Optional[str] = None

class ThreadResponse(ThreadBase):
    id: str
    owner_department_id: str
    owner_agent_id: str
    status: str
    created: str
    budget: int
    thread_goal: Optional[str] = None
    current_milestone: Optional[str] = None
    milestones_log: Optional[str] = "[]"
    favourite_color: Optional[str] = None
    color_theme: Optional[str] = None
    css_pattern: Optional[str] = None
    class Config:
        from_attributes = True

class AgentBase(BaseModel):
    name_id: str
    department_id: Optional[str] = None
    is_ceo: bool = False
    ticks: int = 60
    mode: str = "Points Accounter"
    custom_prompt: Optional[str] = ""

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    mode: Optional[str] = None
    custom_prompt: Optional[str] = None
    memory: Optional[str] = None

class AgentResponse(AgentBase):
    id: str
    born: str
    wallet_current: int
    memory: str
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    name: str
    color: str

class DepartmentResponse(DepartmentBase):
    id: str
    ledger_current: int
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    who: str
    what: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    thread_id: str
    when: str
    points: int
    class Config:
        from_attributes = True

class LogActionResponse(BaseModel):
    id: int
    agent_id: str
    when: str
    what: str
    points: Optional[int]
    class Config:
        from_attributes = True

class CustomPromptEntryCreate(BaseModel):
    title: str
    body: str

class CustomPromptEntryResponse(CustomPromptEntryCreate):
    id: int
    created: str
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class ToolInvokeRequest(BaseModel):
    agent_id: str
    args: str

class AgentToolUpdate(BaseModel):
    enabled: Optional[bool] = None
    config_json: Optional[str] = None

class AgentToolResponse(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool
    config_json: str
    is_custom: bool = False
    owner_id: Optional[str] = None
    price: int = 0
    prompt_template: Optional[str] = None
    args_definition: str = "[]"
    call_tools: str = "[]"
    allowed_actions: str = "[]"
    class Config:
        from_attributes = True

class ToolCreateRequest(BaseModel):
    id: str
    name: str
    description: str
    prompt_template: str = ""
    args_definition: str = "[]"
    call_tools: str = "[]"
    allowed_actions: str = "[]"
    owner_id: Optional[str] = None
    price: int = 0

class TransactionCreate(BaseModel):
    from_id: str
    to_id: str
    amount: int
    reason: str

class SystemLogResponse(BaseModel):
    id: int
    time: str
    level: str
    category: str
    agent_id: Optional[str]
    dept_id: Optional[str]
    event: str
    details: str
    class Config:
        from_attributes = True


# ── Marketplace ───────────────────────────────────────────────────────────────

class MarketplaceToolResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    ownership_price: int = 0
    price: int = 0
    purchase_count: int = 0
    owner_id: Optional[str]
    tags: str = "[]"
    version: str = "1.0"
    enabled: bool
    status: str = "MARKETPLACE"
    workshop_validated: bool = False
    changelog: Optional[str] = None
    class Config:
        from_attributes = True

class ToolOwnershipResponse(BaseModel):
    id: int
    agent_id: str
    tool_id: str
    purchased_at: str
    price_paid: int
    class Config:
        from_attributes = True

class PublishToolRequest(BaseModel):
    ownership_price: int = 0
    price: int = 0
    category: str = "General"
    tags: str = "[]"
    changelog: Optional[str] = None

class WorkshopToolCreate(BaseModel):
    id: str
    name: str
    description: str
    prompt_template: str = ""
    args_definition: str = "[]"
    call_tools: str = "[]"
    allowed_actions: str = "[]"
    category: str = "General"
    tags: str = "[]"
    ownership_price: int = 0
    price: int = 0
