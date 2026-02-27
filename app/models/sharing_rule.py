import enum
from datetime import UTC, datetime

from sqlalchemy import Column, Enum
from sqlmodel import Field, SQLModel


class Visibility(str, enum.Enum):
    BUSY_ONLY = "busy_only"
    DETAILS = "details"
    FULL = "full"


class SharingRule(SQLModel, table=True):
    __tablename__ = "sharing_rules"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    shared_with_id: int | None = Field(default=None, foreign_key="users.id")
    shared_with_email: str | None = None

    visibility: str = Field(sa_column=Column(Enum(Visibility), default=Visibility.BUSY_ONLY))
    tag_filter: str | None = None  # JSON list of tag IDs to share
    is_active: bool = True

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
