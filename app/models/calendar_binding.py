from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class CalendarBinding(SQLModel, table=True):
    __tablename__ = "calendar_bindings"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    study_block_id: int = Field(foreign_key="study_blocks.id", index=True)

    provider: str = "google"
    external_event_id: str = Field(index=True)
    last_synced_hash: str = ""
    last_synced_at: datetime | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
