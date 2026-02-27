from datetime import UTC, datetime
from typing import Optional

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

    # Google Calendar OAuth (separate from Supabase Auth)
    google_access_token: str | None = None
    google_refresh_token: str | None = None
    google_token_expiry: Optional[datetime] = None

    # Calendar
    study_calendar_id: str | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
