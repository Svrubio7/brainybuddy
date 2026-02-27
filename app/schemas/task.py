from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str
    due_date: datetime
    course_id: int | None = None
    description: str = ""
    estimated_hours: float | None = None
    difficulty: int = Field(default=3, ge=1, le=5)
    priority: str = "medium"
    task_type: str = "assignment"
    focus_load: str = "medium"
    splittable: bool = True
    min_block_minutes: int = 30
    max_block_minutes: int = 120
    tag_ids: list[int] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    due_date: datetime | None = None
    course_id: int | None = None
    description: str | None = None
    estimated_hours: float | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    priority: str | None = None
    task_type: str | None = None
    focus_load: str | None = None
    splittable: bool | None = None
    min_block_minutes: int | None = None
    max_block_minutes: int | None = None
    tag_ids: list[int] | None = None


class TaskResponse(BaseModel):
    id: int
    user_id: int
    course_id: int | None
    title: str
    description: str
    due_date: datetime
    estimated_hours: float | None
    difficulty: int
    priority: str
    task_type: str
    focus_load: str
    status: str
    splittable: bool
    min_block_minutes: int
    max_block_minutes: int
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tag_ids: list[int] = []


class AddTimeRequest(BaseModel):
    additional_hours: float = Field(gt=0)
