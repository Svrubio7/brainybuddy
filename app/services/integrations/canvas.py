"""Canvas LMS connector implementation."""

import logging
from datetime import datetime

import httpx

from app.services.integrations.base import LMSConnector

logger = logging.getLogger(__name__)


class CanvasConnector(LMSConnector):
    """Connects to Canvas LMS via its REST API.

    Requires:
        - base_url: The Canvas instance URL (e.g. https://myschool.instructure.com)
        - api_token: A Canvas API access token
    """

    def __init__(self) -> None:
        self.base_url: str = ""
        self.api_token: str = ""
        self._client: httpx.AsyncClient | None = None

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}"}

    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with Canvas using an API token.

        Args:
            credentials: Must include 'base_url' and 'api_token'.
        """
        self.base_url = credentials.get("base_url", "").rstrip("/")
        self.api_token = credentials.get("api_token", "")

        if not self.base_url or not self.api_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/users/self",
                    headers=self.headers,
                    timeout=15,
                )
                if resp.status_code == 200:
                    logger.info("Canvas authentication succeeded.")
                    return True
                logger.warning(
                    "Canvas authentication failed with status %d", resp.status_code
                )
                return False
        except httpx.HTTPError as exc:
            logger.error("Canvas authentication error: %s", exc)
            return False

    async def fetch_courses(self) -> list[dict]:
        """Fetch active courses from Canvas."""
        courses: list[dict] = []
        url = f"{self.base_url}/api/v1/courses"
        params: dict = {
            "enrollment_state": "active",
            "per_page": 100,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url, headers=self.headers, params=params, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()

                for course in data:
                    courses.append({
                        "name": course.get("name", ""),
                        "code": course.get("course_code", ""),
                        "external_id": str(course.get("id", "")),
                        "term": course.get("enrollment_term_id"),
                    })
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch Canvas courses: %s", exc)

        return courses

    async def fetch_assignments(self) -> list[dict]:
        """Fetch assignments from all active courses in Canvas."""
        assignments: list[dict] = []
        courses = await self.fetch_courses()

        try:
            async with httpx.AsyncClient() as client:
                for course in courses:
                    course_id = course["external_id"]
                    url = f"{self.base_url}/api/v1/courses/{course_id}/assignments"
                    params: dict = {"per_page": 100, "order_by": "due_at"}

                    resp = await client.get(
                        url, headers=self.headers, params=params, timeout=30
                    )
                    if resp.status_code != 200:
                        logger.warning(
                            "Skipping assignments for course %s (status %d)",
                            course_id,
                            resp.status_code,
                        )
                        continue

                    data = resp.json()
                    for assignment in data:
                        due_at = assignment.get("due_at")
                        due_date = (
                            datetime.fromisoformat(due_at.replace("Z", "+00:00")).isoformat()
                            if due_at
                            else None
                        )
                        assignments.append({
                            "title": assignment.get("name", ""),
                            "due_date": due_date,
                            "course_name": course["name"],
                            "description": assignment.get("description", "") or "",
                            "points_possible": assignment.get("points_possible"),
                            "external_id": str(assignment.get("id", "")),
                        })
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch Canvas assignments: %s", exc)

        return assignments
