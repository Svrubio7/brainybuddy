from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/google/connect")
async def connect_google(user: CurrentUser, session: DbSession):
    """Connect Google Calendar. Calendar is created during OAuth callback."""
    if user.study_calendar_id:
        return {"status": "connected", "calendar_id": user.study_calendar_id}
    return {"status": "not_connected", "message": "Re-authenticate with Google to connect"}


@router.post("/google/disconnect")
async def disconnect_google(user: CurrentUser, session: DbSession):
    user.study_calendar_id = None
    user.google_access_token = None
    user.google_refresh_token = None
    await session.commit()
    return {"status": "disconnected"}


@router.post("/trigger")
async def trigger_sync(user: CurrentUser, session: DbSession):
    """Trigger a manual sync with Google Calendar."""
    from app.tasks.sync_tasks import sync_blocks_to_google

    if not user.study_calendar_id:
        return {"status": "error", "message": "Google Calendar not connected"}

    sync_blocks_to_google.delay(user.id)
    return {"status": "triggered"}


@router.get("/status")
async def sync_status(user: CurrentUser, session: DbSession):
    return {
        "google_connected": user.study_calendar_id is not None,
        "calendar_id": user.study_calendar_id,
    }
