from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.database import get_session
from app.core.deps import CurrentUser
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthUrl,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.sync.google_calendar import create_study_plan_calendar

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar",
]


def _build_flow() -> Flow:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


@router.get("/google", response_model=GoogleAuthUrl)
async def google_login():
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return GoogleAuthUrl(auth_url=auth_url)


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str,
    session: AsyncSession = Depends(get_session),
):
    flow = _build_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Verify the ID token
    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    google_id = id_info["sub"]
    email = id_info.get("email", "")
    name = id_info.get("name", "")
    picture = id_info.get("picture", "")

    # Upsert user
    result = await session.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            display_name=name,
            avatar_url=picture,
            google_id=google_id,
            google_access_token=credentials.token,
            google_refresh_token=credentials.refresh_token,
            google_token_expiry=credentials.expiry,
        )
        session.add(user)
    else:
        user.google_access_token = credentials.token
        if credentials.refresh_token:
            user.google_refresh_token = credentials.refresh_token
        user.google_token_expiry = credentials.expiry
        user.display_name = name
        user.avatar_url = picture

    await session.commit()
    await session.refresh(user)

    # Create study calendar if needed
    if user.study_calendar_id is None and user.google_access_token:
        try:
            calendar_id = await create_study_plan_calendar(user)
            user.study_calendar_id = calendar_id
            await session.commit()
        except Exception:
            pass  # Non-critical — user can sync later

    # Generate JWT tokens
    token_data = {"sub": str(user.id), "email": user.email}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
):
    payload = verify_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_data = {"sub": str(user.id), "email": user.email}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}


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
