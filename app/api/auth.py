from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.deps import CurrentUser
from app.core.rate_limit import limiter
from app.core.security import verify_supabase_token
from app.models.user import User
from app.schemas.auth import ProvisionRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/provision", response_model=UserResponse)
@limiter.limit("10/minute")
async def provision(
    request: Request,
    body: ProvisionRequest,
    session: AsyncSession = Depends(get_session),
):
    """Called by frontend after Supabase sign-in. Upserts public.users from JWT claims."""
    payload = verify_supabase_token(body.access_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase token",
        )

    sub = payload["sub"]
    email = payload.get("email", "")
    user_metadata = payload.get("user_metadata", {})
    display_name = user_metadata.get("full_name", user_metadata.get("name", ""))
    avatar_url = user_metadata.get("avatar_url", user_metadata.get("picture", ""))

    result = await session.execute(select(User).where(User.supabase_id == sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            supabase_id=sub,
        )
        session.add(user)
    else:
        user.email = email
        user.display_name = display_name or user.display_name
        user.avatar_url = avatar_url or user.avatar_url

    await session.commit()
    await session.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        study_calendar_id=user.study_calendar_id,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        study_calendar_id=user.study_calendar_id,
    )
