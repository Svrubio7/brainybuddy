from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    display_name: str = ""
    avatar_url: str = ""
    timezone: str = "UTC"

    # Supabase Auth
    supabase_id: str = Field(unique=True, index=True)

    # Calendar
    study_calendar_id: str | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
