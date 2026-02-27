"""Todoist sync service.

Syncs BrainyBuddy tasks with Todoist, allowing users to manage
their study plan from either platform.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TODOIST_API_BASE = "https://api.todoist.com/rest/v2"


class TodoistSyncService:
    """Sync BrainyBuddy tasks with Todoist."""

    def __init__(self, api_token: str, project_id: str | None = None) -> None:
        self.api_token = api_token
        self.project_id = project_id  # Optional: restrict sync to one project

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def verify_connection(self) -> bool:
        """Verify that the Todoist token is valid."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{TODOIST_API_BASE}/projects",
                    headers=self.headers,
                    timeout=15,
                )
                if resp.status_code == 200:
                    logger.info("Todoist connection verified.")
                    return True
                logger.warning(
                    "Todoist connection failed with status %d", resp.status_code
                )
                return False
        except httpx.HTTPError as exc:
            logger.error("Todoist connection error: %s", exc)
            return False

    async def fetch_projects(self) -> list[dict]:
        """Fetch all Todoist projects."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{TODOIST_API_BASE}/projects",
                    headers=self.headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                return [
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "color": p.get("color"),
                        "is_favorite": p.get("is_favorite", False),
                    }
                    for p in data
                ]
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch Todoist projects: %s", exc)
            return []

    async def push_tasks(self, tasks: list[dict]) -> list[dict]:
        """Push BrainyBuddy tasks to Todoist.

        Args:
            tasks: List of task dicts with title, due_date, priority, etc.

        Returns:
            List of sync results with Todoist task IDs.
        """
        results: list[dict] = []

        try:
            async with httpx.AsyncClient() as client:
                for task in tasks:
                    payload = self._task_to_todoist(task)

                    todoist_id = task.get("todoist_id")
                    if todoist_id:
                        resp = await client.post(
                            f"{TODOIST_API_BASE}/tasks/{todoist_id}",
                            headers=self.headers,
                            json=payload,
                            timeout=15,
                        )
                    else:
                        resp = await client.post(
                            f"{TODOIST_API_BASE}/tasks",
                            headers=self.headers,
                            json=payload,
                            timeout=15,
                        )

                    if resp.status_code in (200, 204):
                        result_data = resp.json() if resp.status_code == 200 else {}
                        results.append({
                            "task_title": task.get("title", ""),
                            "todoist_id": result_data.get("id", todoist_id),
                            "status": "synced",
                        })
                    else:
                        logger.warning(
                            "Failed to sync task '%s' to Todoist: %s",
                            task.get("title"),
                            resp.text,
                        )
                        results.append({
                            "task_title": task.get("title", ""),
                            "status": "error",
                            "error": resp.text,
                        })
        except httpx.HTTPError as exc:
            logger.error("Todoist push error: %s", exc)

        return results

    async def pull_tasks(self) -> list[dict]:
        """Pull tasks from Todoist into BrainyBuddy format.

        Returns:
            List of task dicts ready for import.
        """
        tasks: list[dict] = []

        try:
            async with httpx.AsyncClient() as client:
                params: dict[str, Any] = {}
                if self.project_id:
                    params["project_id"] = self.project_id

                resp = await client.get(
                    f"{TODOIST_API_BASE}/tasks",
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data:
                    tasks.append(self._todoist_to_task(item))
        except httpx.HTTPError as exc:
            logger.error("Todoist pull error: %s", exc)

        return tasks

    async def sync_bidirectional(
        self, local_tasks: list[dict]
    ) -> dict[str, Any]:
        """Perform a full bidirectional sync.

        Returns:
            Summary with pushed_count, pulled_count, conflicts.
        """
        pushed = await self.push_tasks(local_tasks)
        pulled = await self.pull_tasks()

        pushed_ok = sum(1 for r in pushed if r.get("status") == "synced")

        return {
            "pushed_count": pushed_ok,
            "pushed_errors": len(pushed) - pushed_ok,
            "pulled_count": len(pulled),
            "pulled_tasks": pulled,
            "conflicts": [],  # TODO: implement conflict resolution
        }

    # ---- Private helpers ----

    def _task_to_todoist(self, task: dict) -> dict:
        """Convert a BrainyBuddy task to Todoist task payload."""
        payload: dict[str, Any] = {
            "content": task.get("title", "Untitled"),
            "description": task.get("description", ""),
        }

        if self.project_id:
            payload["project_id"] = self.project_id

        # Map BrainyBuddy priority (1-5) to Todoist priority (1-4, where 4 is highest)
        priority = task.get("priority", 3)
        todoist_priority = min(4, max(1, round(priority * 4 / 5)))
        payload["priority"] = todoist_priority

        due_date = task.get("due_date")
        if due_date:
            payload["due_date"] = (
                due_date if isinstance(due_date, str) else due_date.isoformat()
            )

        return payload

    def _todoist_to_task(self, item: dict) -> dict:
        """Convert a Todoist task to BrainyBuddy task dict."""
        due = item.get("due")
        due_date = due.get("date") if due else None

        # Map Todoist priority (1-4) back to BrainyBuddy (1-5)
        todoist_priority = item.get("priority", 1)
        priority = min(5, max(1, round(todoist_priority * 5 / 4)))

        return {
            "title": item.get("content", ""),
            "description": item.get("description", ""),
            "due_date": due_date,
            "priority": priority,
            "is_completed": item.get("is_completed", False),
            "todoist_id": item.get("id"),
            "project_id": item.get("project_id"),
        }
