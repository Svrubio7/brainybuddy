from pydantic import BaseModel


class ProvisionRequest(BaseModel):
    access_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    avatar_url: str
    timezone: str
    study_calendar_id: str | None
