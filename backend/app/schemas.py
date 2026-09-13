from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    quick_replies: list[str] = []
    state: str
    intent: str | None = None


class SessionRequest(BaseModel):
    session_id: str


class LeadModel(BaseModel):
    id: int
    session_id: str | None
    name: str | None
    phone: str | None
    program: str | None
    created_at: str
