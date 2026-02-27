from datetime import datetime

from pydantic import BaseModel, Field


class TimeLogCreate(BaseModel):
    task_id: int
    study_block_id: int | None = None
    log_type: str = "timer"  # "timer" | "manual"
    start: datetime
    end: datetime | None = None
    duration_minutes: float = Field(default=0, ge=0)


class TimeLogResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    study_block_id: int | None
    log_type: str
    start: datetime
    end: datetime | None
    duration_minutes: float
    created_at: datetime


class FocusTimerStart(BaseModel):
    task_id: int
    study_block_id: int | None = None


class FocusTimerStop(BaseModel):
    time_log_id: int


class InsightResponse(BaseModel):
    id: int
    user_id: int
    course_id: int | None
    week_start: str
    planned_hours: float
    actual_hours: float
    risk_score: float
    created_at: datetime


class EstimationMultiplier(BaseModel):
    course_id: int | None
    task_type: str
    multiplier: float
    sample_count: int
