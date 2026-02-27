from datetime import UTC, datetime

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class AvailabilityGrid(SQLModel, table=True):
    __tablename__ = "availability_grids"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # JSON: 7 days × 96 slots (15-min each) = boolean grid
    # Format: {"monday": [true, true, false, ...], "tuesday": [...], ...}
    grid: str = Field(sa_column=Column(Text, default="{}"))

    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SchedulingRules(SQLModel, table=True):
    __tablename__ = "scheduling_rules"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    daily_max_hours: float = 8.0
    break_after_minutes: int = 90
    break_duration_minutes: int = 15
    max_consecutive_same_subject_minutes: int = 120
    preferred_start_hour: int = 8
    preferred_end_hour: int = 22
    slot_duration_minutes: int = 15

    # Sleep protection
    sleep_start_hour: int = 23
    sleep_end_hour: int = 7

    # Weekend
    lighter_weekends: bool = True
    weekend_max_hours: float = 4.0

    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
