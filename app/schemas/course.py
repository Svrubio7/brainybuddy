from datetime import date, datetime

from pydantic import BaseModel


class CourseCreate(BaseModel):
    name: str
    code: str = ""
    color: str = "#4F46E5"
    term_start: date | None = None
    term_end: date | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    color: str | None = None
    term_start: date | None = None
    term_end: date | None = None
    estimation_multiplier: float | None = None


class CourseResponse(BaseModel):
    id: int
    user_id: int
    name: str
    code: str
    color: str
    term_start: date | None
    term_end: date | None
    estimation_multiplier: float
    created_at: datetime
    updated_at: datetime
