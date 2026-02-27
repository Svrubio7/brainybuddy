import hashlib
import json
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.user import User


def _get_credentials(user: "User") -> Credentials:
    return Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )


def _get_service(user: "User"):
    credentials = _get_credentials(user)
    return build("calendar", "v3", credentials=credentials)


async def create_study_plan_calendar(user: "User") -> str:
    service = _get_service(user)
    calendar_body = {
        "summary": "Study Plan (BrainyBuddy)",
        "description": "Auto-managed by BrainyBuddy study planner",
        "timeZone": user.timezone or "UTC",
    }
    created = service.calendars().insert(body=calendar_body).execute()
    return created["id"]


async def push_block_to_google(
    user: "User",
    block_id: int,
    task_title: str,
    course_name: str,
    start_iso: str,
    end_iso: str,
) -> str:
    if not user.study_calendar_id:
        raise ValueError("User has no study calendar configured")

    service = _get_service(user)
    event_body = {
        "summary": f"📚 {task_title}" + (f" ({course_name})" if course_name else ""),
        "start": {"dateTime": start_iso, "timeZone": user.timezone or "UTC"},
        "end": {"dateTime": end_iso, "timeZone": user.timezone or "UTC"},
        "extendedProperties": {
            "private": {
                "brainybuddy_block_id": str(block_id),
            }
        },
    }
    event = (
        service.events()
        .insert(calendarId=user.study_calendar_id, body=event_body)
        .execute()
    )
    return event["id"]


async def update_google_event(
    user: "User",
    event_id: str,
    task_title: str,
    course_name: str,
    start_iso: str,
    end_iso: str,
) -> None:
    if not user.study_calendar_id:
        return

    service = _get_service(user)
    event_body = {
        "summary": f"📚 {task_title}" + (f" ({course_name})" if course_name else ""),
        "start": {"dateTime": start_iso, "timeZone": user.timezone or "UTC"},
        "end": {"dateTime": end_iso, "timeZone": user.timezone or "UTC"},
    }
    service.events().patch(
        calendarId=user.study_calendar_id,
        eventId=event_id,
        body=event_body,
    ).execute()


async def delete_google_event(user: "User", event_id: str) -> None:
    if not user.study_calendar_id:
        return

    service = _get_service(user)
    service.events().delete(
        calendarId=user.study_calendar_id, eventId=event_id
    ).execute()


async def pull_changes_from_google(user: "User", sync_token: str | None = None) -> list[dict]:
    if not user.study_calendar_id:
        return []

    service = _get_service(user)
    kwargs = {
        "calendarId": user.study_calendar_id,
        "singleEvents": True,
        "maxResults": 250,
    }
    if sync_token:
        kwargs["syncToken"] = sync_token

    events = service.events().list(**kwargs).execute()
    return events.get("items", [])


def compute_event_hash(event: dict) -> str:
    relevant = {
        "summary": event.get("summary", ""),
        "start": event.get("start", {}),
        "end": event.get("end", {}),
        "status": event.get("status", ""),
    }
    return hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()[:16]
