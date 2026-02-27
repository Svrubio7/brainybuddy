from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class StudyBlock(SQLModel, table=True):
    __tablename__ = "study_blocks"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    plan_version_id: int | None = Field(default=None, foreign_key="plan_versions.id", index=True)

    start: datetime
    end: datetime
    block_index: int = 0
    is_pinned: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
