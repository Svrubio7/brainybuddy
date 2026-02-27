from datetime import datetime

from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    color: str = "#6B7280"


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagResponse(BaseModel):
    id: int
    user_id: int
    name: str
    color: str
    created_at: datetime
