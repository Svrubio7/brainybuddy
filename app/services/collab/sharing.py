"""
Sharing and collaboration service.

Manages sharing rules that let users expose parts of their schedule
to other users with configurable visibility levels.
"""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.sharing_rule import SharingRule, Visibility
from app.models.study_block import StudyBlock
from app.models.task import Task
from app.models.user import User


# ── Request / response schemas ───────────────────────────────────────


class SharingRuleCreate(BaseModel):
    shared_with_email: str
    visibility: str = Visibility.BUSY_ONLY.value
    tag_filter: list[int] | None = None


class SharingRuleResponse(BaseModel):
    id: int
    owner_id: int
    shared_with_id: int | None
    shared_with_email: str | None
    visibility: str
    tag_filter: list[int] | None
    is_active: bool
    created_at: datetime


class SharedBlockResponse(BaseModel):
    """A study block as seen by a viewer — detail depends on visibility."""

    start: datetime
    end: datetime
    # Only present when visibility >= DETAILS
    task_title: str | None = None
    course_name: str | None = None
    # Only present when visibility == FULL
    task_description: str | None = None


# ── Service functions ────────────────────────────────────────────────


async def create_sharing_rule(
    session: AsyncSession,
    owner_id: int,
    data: SharingRuleCreate,
) -> SharingRule:
    """Create a new sharing rule for the given owner."""
    # Resolve email → user id (if the user is already registered)
    result = await session.execute(
        select(User).where(User.email == data.shared_with_email)
    )
    target_user = result.scalar_one_or_none()
    shared_with_id = target_user.id if target_user else None

    # Prevent sharing with yourself
    if shared_with_id is not None and shared_with_id == owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share with yourself.",
        )

    rule = SharingRule(
        owner_id=owner_id,
        shared_with_id=shared_with_id,
        shared_with_email=data.shared_with_email,
        visibility=data.visibility,
        tag_filter=json.dumps(data.tag_filter) if data.tag_filter else None,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def list_my_sharing_rules(
    session: AsyncSession,
    owner_id: int,
) -> list[SharingRule]:
    """List all sharing rules created by the owner."""
    result = await session.execute(
        select(SharingRule).where(SharingRule.owner_id == owner_id)
    )
    return list(result.scalars().all())


async def list_shared_with_me(
    session: AsyncSession,
    user_id: int,
) -> list[SharingRule]:
    """List all rules where someone has shared their schedule with this user."""
    # Match by user id or by email
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return []

    result = await session.execute(
        select(SharingRule).where(
            SharingRule.is_active == True,  # noqa: E712
            (SharingRule.shared_with_id == user_id)
            | (SharingRule.shared_with_email == user.email),
        )
    )
    return list(result.scalars().all())


async def delete_sharing_rule(
    session: AsyncSession,
    owner_id: int,
    rule_id: int,
) -> bool:
    """Delete (deactivate) a sharing rule. Only the owner may do this."""
    result = await session.execute(
        select(SharingRule).where(
            SharingRule.id == rule_id, SharingRule.owner_id == owner_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        return False

    rule.is_active = False
    await session.commit()
    return True


async def get_shared_schedule(
    session: AsyncSession,
    rule_id: int,
    viewer_id: int,
) -> list[SharedBlockResponse]:
    """
    Get the schedule shared via a specific rule.

    Respects visibility levels:
      - BUSY_ONLY  : only start/end times
      - DETAILS    : + task title, course name
      - FULL       : + task description
    """
    # Load the rule and verify the viewer is authorised
    rule_result = await session.execute(
        select(SharingRule).where(SharingRule.id == rule_id, SharingRule.is_active == True)  # noqa: E712
    )
    rule = rule_result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Sharing rule not found")

    # Check the viewer matches
    viewer_result = await session.execute(select(User).where(User.id == viewer_id))
    viewer = viewer_result.scalar_one_or_none()
    if not viewer:
        raise HTTPException(status_code=404, detail="Viewer not found")

    is_authorised = (
        rule.shared_with_id == viewer_id
        or rule.shared_with_email == viewer.email
    )
    if not is_authorised:
        raise HTTPException(status_code=403, detail="Not authorised to view this schedule")

    # Load blocks for the schedule owner
    owner_id = rule.owner_id
    blocks_result = await session.execute(
        select(StudyBlock)
        .where(StudyBlock.user_id == owner_id)
        .order_by(StudyBlock.start)
    )
    blocks = list(blocks_result.scalars().all())

    # If there is a tag filter, we need to filter blocks by task tags
    tag_filter: list[int] | None = None
    if rule.tag_filter:
        try:
            tag_filter = json.loads(rule.tag_filter)
        except Exception:
            tag_filter = None

    # Pre-load tasks for enrichment
    task_ids = {b.task_id for b in blocks}
    tasks_by_id: dict[int, Task] = {}
    if task_ids:
        tasks_result = await session.execute(
            select(Task).where(Task.id.in_(task_ids))  # type: ignore[attr-defined]
        )
        for t in tasks_result.scalars().all():
            tasks_by_id[t.id] = t

    # Build responses according to visibility level
    visibility = rule.visibility
    responses: list[SharedBlockResponse] = []

    for block in blocks:
        task = tasks_by_id.get(block.task_id)

        # Apply tag filter if set (skip blocks whose task doesn't match)
        if tag_filter and task:
            # Tag filtering would require a join with TaskTag — for now
            # we include all blocks.  A future enhancement can filter here.
            pass

        item = SharedBlockResponse(start=block.start, end=block.end)

        if visibility in (Visibility.DETAILS.value, Visibility.FULL.value, "details", "full"):
            item.task_title = task.title if task else None
            # Course name would require another join; left as None for now.
            item.course_name = None

        if visibility in (Visibility.FULL.value, "full"):
            item.task_description = task.description if task else None

        responses.append(item)

    return responses


def _rule_to_response(rule: SharingRule) -> SharingRuleResponse:
    """Convert a SharingRule ORM object to a response schema."""
    tag_ids: list[int] | None = None
    if rule.tag_filter:
        try:
            tag_ids = json.loads(rule.tag_filter)
        except Exception:
            tag_ids = None

    return SharingRuleResponse(
        id=rule.id,
        owner_id=rule.owner_id,
        shared_with_id=rule.shared_with_id,
        shared_with_email=rule.shared_with_email,
        visibility=rule.visibility,
        tag_filter=tag_ids,
        is_active=rule.is_active,
        created_at=rule.created_at,
    )
