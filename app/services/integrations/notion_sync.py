"""Notion bidirectional sync service.

Syncs BrainyBuddy tasks and study blocks with a Notion database,
allowing users to manage their study plan from either side.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionSyncService:
    """Bidirectional sync between BrainyBuddy and a Notion database."""

    def __init__(self, access_token: str, database_id: str) -> None:
        self.access_token = access_token
        self.database_id = database_id

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def verify_connection(self) -> bool:
        """Verify that the Notion token and database are accessible."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{NOTION_API_BASE}/databases/{self.database_id}",
                    headers=self.headers,
                    timeout=15,
                )
                if resp.status_code == 200:
                    logger.info("Notion connection verified for database %s", self.database_id)
                    return True
                logger.warning(
                    "Notion connection failed with status %d: %s",
                    resp.status_code,
                    resp.text,
                )
                return False
        except httpx.HTTPError as exc:
            logger.error("Notion connection error: %s", exc)
            return False

    async def push_tasks(self, tasks: list[dict]) -> list[dict]:
        """Push BrainyBuddy tasks to Notion as pages in the connected database.

        Args:
            tasks: List of task dicts with title, due_date, status, priority, etc.

        Returns:
            List of created/updated Notion page references with external IDs.
        """
        results: list[dict] = []

        try:
            async with httpx.AsyncClient() as client:
                for task in tasks:
                    properties = self._task_to_notion_properties(task)
                    payload = {
                        "parent": {"database_id": self.database_id},
                        "properties": properties,
                    }

                    # If we have an existing Notion page ID, update; otherwise create
                    notion_page_id = task.get("notion_page_id")
                    if notion_page_id:
                        resp = await client.patch(
                            f"{NOTION_API_BASE}/pages/{notion_page_id}",
                            headers=self.headers,
                            json={"properties": properties},
                            timeout=15,
                        )
                    else:
                        resp = await client.post(
                            f"{NOTION_API_BASE}/pages",
                            headers=self.headers,
                            json=payload,
                            timeout=15,
                        )

                    if resp.status_code in (200, 201):
                        page_data = resp.json()
                        results.append({
                            "task_title": task.get("title", ""),
                            "notion_page_id": page_data.get("id"),
                            "status": "synced",
                        })
                    else:
                        logger.warning(
                            "Failed to sync task '%s' to Notion: %s",
                            task.get("title"),
                            resp.text,
                        )
                        results.append({
                            "task_title": task.get("title", ""),
                            "status": "error",
                            "error": resp.text,
                        })
        except httpx.HTTPError as exc:
            logger.error("Notion push error: %s", exc)

        return results

    async def pull_tasks(self) -> list[dict]:
        """Pull tasks from the Notion database into BrainyBuddy format.

        Returns:
            List of task dicts ready for import.
        """
        tasks: list[dict] = []

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{NOTION_API_BASE}/databases/{self.database_id}/query",
                    headers=self.headers,
                    json={},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                for page in data.get("results", []):
                    task = self._notion_page_to_task(page)
                    if task:
                        tasks.append(task)
        except httpx.HTTPError as exc:
            logger.error("Notion pull error: %s", exc)

        return tasks

    async def sync_bidirectional(
        self, local_tasks: list[dict]
    ) -> dict[str, Any]:
        """Perform a full bidirectional sync.

        Pushes local changes to Notion and pulls remote changes back.

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

    def _task_to_notion_properties(self, task: dict) -> dict:
        """Convert a BrainyBuddy task dict to Notion page properties."""
        properties: dict[str, Any] = {
            "Name": {
                "title": [{"text": {"content": task.get("title", "Untitled")}}]
            },
            "Status": {
                "select": {"name": task.get("status", "active")}
            },
            "Priority": {
                "number": task.get("priority", 3)
            },
        }

        due_date = task.get("due_date")
        if due_date:
            properties["Due Date"] = {
                "date": {"start": due_date if isinstance(due_date, str) else due_date.isoformat()}
            }

        return properties

    def _notion_page_to_task(self, page: dict) -> dict | None:
        """Convert a Notion page to a BrainyBuddy task dict."""
        props = page.get("properties", {})

        # Extract title
        title_prop = props.get("Name", {}).get("title", [])
        title = title_prop[0]["text"]["content"] if title_prop else None
        if not title:
            return None

        # Extract due date
        due_date_prop = props.get("Due Date", {}).get("date")
        due_date = due_date_prop.get("start") if due_date_prop else None

        # Extract status
        status_prop = props.get("Status", {}).get("select")
        status = status_prop.get("name") if status_prop else "active"

        # Extract priority
        priority_prop = props.get("Priority", {}).get("number")
        priority = priority_prop if priority_prop is not None else 3

        return {
            "title": title,
            "due_date": due_date,
            "status": status,
            "priority": priority,
            "notion_page_id": page.get("id"),
            "last_edited": page.get("last_edited_time"),
        }
