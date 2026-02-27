import enum
from datetime import UTC, datetime

from sqlalchemy import Column, Enum, Text
from sqlmodel import Field, SQLModel


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = "New Chat"
    is_active: bool = True

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_sessions.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    role: str = Field(sa_column=Column(Enum(MessageRole), default=MessageRole.USER))
    content: str = Field(sa_column=Column(Text, default=""))
    tool_calls: str = Field(sa_column=Column(Text, default=""))  # JSON

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
