from datetime import datetime

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class PlanVersion(SQLModel, table=True):
    __tablename__ = "plan_versions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    version_number: int
    trigger: str = ""  # e.g., "manual_replan", "drag_move", "chat_action", "new_task"
    snapshot: str = Field(sa_column=Column(Text, default=""))  # JSON snapshot of all blocks
    diff_summary: str = ""  # Human-readable summary

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
