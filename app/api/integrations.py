"""API routes for external integrations (LMS, Notion, Todoist, holidays)."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


# ---- Request / Response schemas ----


class LMSConnectRequest(BaseModel):
    base_url: str
    api_token: str | None = None  # Canvas
    token: str | None = None  # Moodle


class IntegrationStatus(BaseModel):
    provider: str
    connected: bool
    last_synced: str | None = None


class SyncResult(BaseModel):
    provider: str
    courses_synced: int
    assignments_synced: int
    errors: list[str] = []


class HolidayEntry(BaseModel):
    date: str
    name: str


class ReducedAvailabilityEntry(BaseModel):
    date: str
    reason: str
    availability_factor: float
    type: str


# ---- List connected integrations ----


@router.get("", response_model=list[IntegrationStatus])
async def list_integrations(user: CurrentUser, session: DbSession):
    """List all available integrations and their connection status."""
    # TODO: read real connection state from a user_integrations table
    integrations = [
        IntegrationStatus(provider="canvas", connected=False),
        IntegrationStatus(provider="moodle", connected=False),
        IntegrationStatus(provider="notion", connected=False),
        IntegrationStatus(provider="todoist", connected=False),
        IntegrationStatus(
            provider="google_calendar",
            connected=user.study_calendar_id is not None,
        ),
    ]
    return integrations


# ---- Canvas ----


@router.post("/canvas/connect")
async def connect_canvas(data: LMSConnectRequest, user: CurrentUser, session: DbSession):
    """Connect a Canvas LMS instance."""
    from app.services.integrations.canvas import CanvasConnector

    connector = CanvasConnector()
    credentials = {
        "base_url": data.base_url,
        "api_token": data.api_token or "",
    }
    authenticated = await connector.authenticate(credentials)
    if not authenticated:
        raise HTTPException(
            status_code=400,
            detail="Failed to authenticate with Canvas. Check your base URL and API token.",
        )

    # TODO: persist the connection in a user_integrations table
    return {"status": "connected", "provider": "canvas"}


@router.post("/canvas/sync", response_model=SyncResult)
async def sync_canvas(data: LMSConnectRequest, user: CurrentUser, session: DbSession):
    """Trigger a sync of courses and assignments from Canvas."""
    from app.services.integrations.canvas import CanvasConnector

    connector = CanvasConnector()
    credentials = {
        "base_url": data.base_url,
        "api_token": data.api_token or "",
    }
    authenticated = await connector.authenticate(credentials)
    if not authenticated:
        raise HTTPException(status_code=400, detail="Canvas authentication failed.")

    courses = await connector.fetch_courses()
    assignments = await connector.fetch_assignments()

    # TODO: upsert courses and assignments into BrainyBuddy DB
    errors: list[str] = []

    return SyncResult(
        provider="canvas",
        courses_synced=len(courses),
        assignments_synced=len(assignments),
        errors=errors,
    )


# ---- Moodle ----


@router.post("/moodle/connect")
async def connect_moodle(data: LMSConnectRequest, user: CurrentUser, session: DbSession):
    """Connect a Moodle LMS instance."""
    from app.services.integrations.moodle import MoodleConnector

    connector = MoodleConnector()
    credentials = {
        "base_url": data.base_url,
        "token": data.token or "",
    }
    authenticated = await connector.authenticate(credentials)
    if not authenticated:
        raise HTTPException(
            status_code=400,
            detail="Failed to authenticate with Moodle. Check your base URL and token.",
        )

    # TODO: persist the connection in a user_integrations table
    return {"status": "connected", "provider": "moodle"}


@router.post("/moodle/sync", response_model=SyncResult)
async def sync_moodle(data: LMSConnectRequest, user: CurrentUser, session: DbSession):
    """Trigger a sync of courses and assignments from Moodle."""
    from app.services.integrations.moodle import MoodleConnector

    connector = MoodleConnector()
    credentials = {
        "base_url": data.base_url,
        "token": data.token or "",
    }
    authenticated = await connector.authenticate(credentials)
    if not authenticated:
        raise HTTPException(status_code=400, detail="Moodle authentication failed.")

    courses = await connector.fetch_courses()
    assignments = await connector.fetch_assignments()

    # TODO: upsert courses and assignments into BrainyBuddy DB
    errors: list[str] = []

    return SyncResult(
        provider="moodle",
        courses_synced=len(courses),
        assignments_synced=len(assignments),
        errors=errors,
    )


# ---- Holidays ----


@router.get("/holidays", response_model=list[HolidayEntry])
async def get_holidays_endpoint(
    user: CurrentUser,
    session: DbSession,
    country: str = Query(default="US", min_length=2, max_length=2),
    year: int = Query(default=None),
    state: str | None = Query(default=None),
):
    """Get public holidays for a country and year."""
    from app.services.integrations.holiday_detection import get_holidays

    if year is None:
        year = datetime.now(timezone.utc).year

    holiday_list = get_holidays(country=country, year=year, state=state)
    return [HolidayEntry(date=h["date"], name=h["name"]) for h in holiday_list]


@router.get("/holidays/reduced-availability", response_model=list[ReducedAvailabilityEntry])
async def get_reduced_availability(
    user: CurrentUser,
    session: DbSession,
    start_date: date = Query(...),
    end_date: date = Query(...),
    country: str = Query(default="US", min_length=2, max_length=2),
    state: str | None = Query(default=None),
):
    """Detect dates with reduced study availability (holidays, travel, breaks)."""
    from app.services.integrations.holiday_detection import detect_reduced_availability

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    results = await detect_reduced_availability(
        user_id=user.id,
        date_range=(start_date, end_date),
        country=country,
        state=state,
    )
    return [
        ReducedAvailabilityEntry(
            date=r["date"],
            reason=r["reason"],
            availability_factor=r["availability_factor"],
            type=r["type"],
        )
        for r in results
    ]
