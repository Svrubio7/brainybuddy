from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class GoogleAuthUrl(BaseModel):
    auth_url: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    avatar_url: str
    timezone: str
    study_calendar_id: str | None
