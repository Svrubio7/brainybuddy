from datetime import datetime

from pydantic import BaseModel


class StudyBlockResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    plan_version_id: int | None
    start: datetime
    end: datetime
    block_index: int
    is_pinned: bool
    created_at: datetime
    task_title: str = ""
    course_name: str = ""
    course_color: str = ""


class MoveBlockRequest(BaseModel):
    start: datetime
    end: datetime


class PlanDiffItem(BaseModel):
    action: str  # "added", "moved", "deleted"
    block_id: int | None = None
    task_title: str = ""
    old_start: datetime | None = None
    old_end: datetime | None = None
    new_start: datetime | None = None
    new_end: datetime | None = None


class PlanDiffResponse(BaseModel):
    added: int = 0
    moved: int = 0
    deleted: int = 0
    items: list[PlanDiffItem] = []
    plan_version_id: int | None = None


class PlanVersionResponse(BaseModel):
    id: int
    version_number: int
    trigger: str
    diff_summary: str
    created_at: datetime


class GeneratePlanRequest(BaseModel):
    reason: str = "manual_replan"
