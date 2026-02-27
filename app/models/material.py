import enum
from datetime import UTC, datetime

from sqlalchemy import Column, Enum
from sqlmodel import Field, SQLModel


class ExtractionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Material(SQLModel, table=True):
    __tablename__ = "materials"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    course_id: int | None = Field(default=None, foreign_key="courses.id")

    filename: str
    content_type: str = ""
    file_size: int = 0
    s3_key: str = ""

    extraction_status: str = Field(
        sa_column=Column(Enum(ExtractionStatus), default=ExtractionStatus.PENDING)
    )
    extracted_text: str = ""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
