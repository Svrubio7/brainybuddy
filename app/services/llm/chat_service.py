"""LLM Chat service using Anthropic SDK with tool-calling."""

import json
from datetime import datetime

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.task import Task
from app.services.llm.tools import TOOLS

SYSTEM_PROMPT = """You are BrainyBuddy, an AI study planning assistant. You help students manage their academic workload by:
- Creating and updating study tasks
- Adjusting scheduling constraints
- Triggering replans when needed
- Marking tasks as done

You have access to tools that let you take actions on the student's study plan.
When a student describes tasks, deadlines, or schedule changes, use the appropriate tool.
Always be encouraging and supportive. Keep responses concise.

Current date/time: {now}

Student's active tasks:
{tasks_context}
"""


async def _get_tasks_context(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.status == "active")
        .order_by(Task.due_date)
    )
    tasks = result.scalars().all()
    if not tasks:
        return "No active tasks."
    lines = []
    for t in tasks:
        lines.append(
            f"- [ID:{t.id}] {t.title} | Due: {t.due_date.strftime('%Y-%m-%d')} | "
            f"Est: {t.estimated_hours or '?'}h | Priority: {t.priority}"
        )
    return "\n".join(lines)


async def get_or_create_session(
    session: AsyncSession, user_id: int, session_id: int | None = None
) -> ChatSession:
    if session_id:
        result = await session.execute(
            select(ChatSession).where(
                ChatSession.id == session_id, ChatSession.user_id == user_id
            )
        )
        chat_session = result.scalar_one_or_none()
        if chat_session:
            return chat_session

    chat_session = ChatSession(user_id=user_id)
    session.add(chat_session)
    await session.flush()
    return chat_session


async def get_chat_history(
    session: AsyncSession, user_id: int, session_id: int, limit: int = 50
) -> list[ChatMessage]:
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id, ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    )
    return list(result.scalars().all())


async def chat(
    session: AsyncSession,
    user_id: int,
    message: str,
    session_id: int | None = None,
) -> tuple[str, list[dict], int]:
    """
    Process a chat message. Returns (response_text, tool_calls, session_id).
    """
    chat_session = await get_or_create_session(session, user_id, session_id)

    # Save user message
    user_msg = ChatMessage(
        session_id=chat_session.id,
        user_id=user_id,
        role=MessageRole.USER,
        content=message,
    )
    session.add(user_msg)
    await session.flush()

    # Build context
    tasks_context = await _get_tasks_context(session, user_id)
    system = SYSTEM_PROMPT.format(
        now=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        tasks_context=tasks_context,
    )

    # Get recent history for context
    history = await get_chat_history(session, user_id, chat_session.id, limit=20)
    messages = []
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # Call Anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system,
        messages=messages,
        tools=TOOLS,
    )

    # Extract response
    response_text = ""
    tool_calls = []

    for block in response.content:
        if block.type == "text":
            response_text += block.text
        elif block.type == "tool_use":
            tool_calls.append({
                "name": block.name,
                "arguments": block.input,
            })

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=chat_session.id,
        user_id=user_id,
        role=MessageRole.ASSISTANT,
        content=response_text,
        tool_calls=json.dumps(tool_calls) if tool_calls else "",
    )
    session.add(assistant_msg)
    await session.commit()

    return response_text, tool_calls, chat_session.id
