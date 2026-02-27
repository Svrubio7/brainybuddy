import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.deps import CurrentUser, DbSession
from app.schemas.chat import ChatMessageResponse, ChatRequest, ChatSessionResponse, ToolCallInfo
from app.services.llm import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatMessageResponse)
async def send_message(data: ChatRequest, user: CurrentUser, session: DbSession):
    response_text, tool_calls, session_id = await chat_service.chat(
        session, user.id, data.message, data.session_id
    )
    return ChatMessageResponse(
        id=0,
        session_id=session_id,
        role="assistant",
        content=response_text,
        tool_calls=[
            ToolCallInfo(name=tc["name"], arguments=tc["arguments"]) for tc in tool_calls
        ],
        created_at=__import__("datetime").datetime.utcnow(),
    )


@router.post("/stream")
async def send_message_stream(data: ChatRequest, user: CurrentUser, session: DbSession):
    """SSE streaming endpoint for chat responses."""

    async def event_generator():
        response_text, tool_calls, session_id = await chat_service.chat(
            session, user.id, data.message, data.session_id
        )

        # Send text chunks
        yield f"data: {json.dumps({'type': 'text', 'content': response_text})}\n\n"

        # Send tool calls
        for tc in tool_calls:
            yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'arguments': tc['arguments']})}\n\n"

        # Done
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history", response_model=list[ChatMessageResponse])
async def get_history(
    user: CurrentUser,
    session: DbSession,
    session_id: int | None = None,
):
    if not session_id:
        return []

    messages = await chat_service.get_chat_history(session, user.id, session_id)
    return [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            tool_calls=(
                [ToolCallInfo(**tc) for tc in json.loads(m.tool_calls)]
                if m.tool_calls
                else []
            ),
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def get_sessions(user: CurrentUser, session: DbSession):
    from sqlmodel import select
    from app.models.chat import ChatSession

    result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]
