"""Abstract base class for LMS connectors."""

from abc import ABC, abstractmethod


class LMSConnector(ABC):
    """Base interface for all LMS integrations (Canvas, Moodle, etc.)."""

    @abstractmethod
    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with the LMS using the provided credentials.

        Args:
            credentials: Dict containing provider-specific auth info
                         (e.g. api_key, base_url, token).

        Returns:
            True if authentication succeeded, False otherwise.
        """
        ...

    @abstractmethod
    async def fetch_assignments(self) -> list[dict]:
        """Fetch all assignments from the connected LMS.

        Returns:
            List of dicts, each with at minimum:
                - title: str
                - due_date: str (ISO 8601)
                - course_name: str
                - description: str
                - points_possible: float | None
                - external_id: str
        """
        ...

    @abstractmethod
    async def fetch_courses(self) -> list[dict]:
        """Fetch all courses the user is enrolled in.

        Returns:
            List of dicts, each with at minimum:
                - name: str
                - code: str
                - external_id: str
                - term: str | None
        """
        ...
