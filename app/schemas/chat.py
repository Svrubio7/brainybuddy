from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


class ToolCallInfo(BaseModel):
    name: str
    arguments: dict
    result: dict | None = None


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    tool_calls: list[ToolCallInfo] = []
    created_at: datetime


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
