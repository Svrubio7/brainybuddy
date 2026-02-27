"""Moodle LMS connector implementation."""

import logging
from datetime import datetime, timezone

import httpx

from app.services.integrations.base import LMSConnector

logger = logging.getLogger(__name__)


class MoodleConnector(LMSConnector):
    """Connects to Moodle via its Web Services REST API.

    Requires:
        - base_url: The Moodle instance URL (e.g. https://moodle.myschool.edu)
        - token: A Moodle web-service token
    """

    def __init__(self) -> None:
        self.base_url: str = ""
        self.token: str = ""
        self._user_id: int | None = None

    def _ws_url(self, function: str) -> str:
        return (
            f"{self.base_url}/webservice/rest/server.php"
            f"?wstoken={self.token}"
            f"&wsfunction={function}"
            f"&moodlewsrestformat=json"
        )

    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with Moodle using a web-service token.

        Args:
            credentials: Must include 'base_url' and 'token'.
        """
        self.base_url = credentials.get("base_url", "").rstrip("/")
        self.token = credentials.get("token", "")

        if not self.base_url or not self.token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._ws_url("core_webservice_get_site_info"),
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

                if "errorcode" in data:
                    logger.warning("Moodle auth error: %s", data.get("message"))
                    return False

                self._user_id = data.get("userid")
                logger.info(
                    "Moodle authentication succeeded for user %s", self._user_id
                )
                return True
        except httpx.HTTPError as exc:
            logger.error("Moodle authentication error: %s", exc)
            return False

    async def fetch_courses(self) -> list[dict]:
        """Fetch enrolled courses from Moodle."""
        courses: list[dict] = []

        if self._user_id is None:
            logger.error("Cannot fetch courses: not authenticated.")
            return courses

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._ws_url("core_enrol_get_users_courses")
                    + f"&userid={self._user_id}",
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                if isinstance(data, dict) and "errorcode" in data:
                    logger.warning("Moodle courses error: %s", data.get("message"))
                    return courses

                for course in data:
                    courses.append({
                        "name": course.get("fullname", ""),
                        "code": course.get("shortname", ""),
                        "external_id": str(course.get("id", "")),
                        "term": None,
                    })
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch Moodle courses: %s", exc)

        return courses

    async def fetch_assignments(self) -> list[dict]:
        """Fetch assignments from all enrolled Moodle courses."""
        assignments: list[dict] = []
        courses = await self.fetch_courses()

        if not courses:
            return assignments

        course_ids = [c["external_id"] for c in courses]
        course_name_map = {c["external_id"]: c["name"] for c in courses}

        try:
            async with httpx.AsyncClient() as client:
                # Build courseids[] params
                course_params = "&".join(
                    f"courseids[]={cid}" for cid in course_ids
                )
                url = (
                    self._ws_url("mod_assign_get_assignments")
                    + f"&{course_params}"
                )
                resp = await client.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                if isinstance(data, dict) and "errorcode" in data:
                    logger.warning(
                        "Moodle assignments error: %s", data.get("message")
                    )
                    return assignments

                for course_block in data.get("courses", []):
                    course_id = str(course_block.get("id", ""))
                    course_name = course_name_map.get(course_id, "")
                    for assignment in course_block.get("assignments", []):
                        due_date_ts = assignment.get("duedate", 0)
                        due_date = (
                            datetime.fromtimestamp(
                                due_date_ts, tz=timezone.utc
                            ).isoformat()
                            if due_date_ts
                            else None
                        )
                        assignments.append({
                            "title": assignment.get("name", ""),
                            "due_date": due_date,
                            "course_name": course_name,
                            "description": assignment.get("intro", "") or "",
                            "points_possible": assignment.get("grade"),
                            "external_id": str(assignment.get("id", "")),
                        })
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch Moodle assignments: %s", exc)

        return assignments
