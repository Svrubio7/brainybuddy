from datetime import datetime, date

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    __tablename__ = "courses"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str
    code: str = ""
    color: str = "#4F46E5"
    term_start: date | None = None
    term_end: date | None = None
    estimation_multiplier: float = 1.0

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
