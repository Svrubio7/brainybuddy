import enum
from datetime import datetime

from sqlalchemy import Column, Enum
from sqlmodel import Field, SQLModel


class LogType(str, enum.Enum):
    TIMER = "timer"
    MANUAL = "manual"


class TimeLog(SQLModel, table=True):
    __tablename__ = "time_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    study_block_id: int | None = Field(default=None, foreign_key="study_blocks.id")

    log_type: str = Field(sa_column=Column(Enum(LogType), default=LogType.TIMER))
    start: datetime
    end: datetime | None = None
    duration_minutes: float = 0

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
