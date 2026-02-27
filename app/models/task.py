import enum
from datetime import UTC, datetime

from sqlalchemy import Column, Enum
from sqlmodel import Field, SQLModel


class TaskStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskType(str, enum.Enum):
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    READING = "reading"
    PROJECT = "project"
    OTHER = "other"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FocusLoad(str, enum.Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    DEEP = "deep"


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    course_id: int | None = Field(default=None, foreign_key="courses.id", index=True)

    title: str
    description: str = ""
    due_date: datetime
    estimated_hours: float | None = None
    difficulty: int = Field(default=3, ge=1, le=5)
    priority: str = Field(sa_column=Column(Enum(Priority), default=Priority.MEDIUM))
    task_type: str = Field(sa_column=Column(Enum(TaskType), default=TaskType.ASSIGNMENT))
    focus_load: str = Field(sa_column=Column(Enum(FocusLoad), default=FocusLoad.MEDIUM))
    status: str = Field(sa_column=Column(Enum(TaskStatus), default=TaskStatus.ACTIVE))

    # Split rules (stored as simple fields)
    splittable: bool = True
    min_block_minutes: int = 30
    max_block_minutes: int = 120

    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
