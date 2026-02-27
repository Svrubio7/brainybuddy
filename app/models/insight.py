from datetime import UTC, datetime, date

from sqlmodel import Field, SQLModel


class Insight(SQLModel, table=True):
    __tablename__ = "insights"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    course_id: int | None = Field(default=None, foreign_key="courses.id")

    week_start: date
    planned_hours: float = 0
    actual_hours: float = 0
    risk_score: float = 0  # 0-1, higher = more at risk

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
