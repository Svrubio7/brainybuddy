from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.course import Course
from app.models.study_block import StudyBlock
from app.models.task import Task
from app.schemas.availability import AvailabilityGridSchema, SchedulingRulesSchema
from app.schemas.schedule import PlanDiffResponse
from app.services.availability_service import get_availability_grid, get_scheduling_rules
from app.services.plan_versioning import create_plan_version
from app.services.scheduler.diff import compute_diff
from app.services.scheduler.engine import ScheduledBlock, generate_plan


async def get_task_titles(session: AsyncSession, user_id: int) -> dict[int, str]:
    result = await session.execute(select(Task).where(Task.user_id == user_id))
    return {t.id: t.title for t in result.scalars().all()}


async def get_current_blocks(session: AsyncSession, user_id: int) -> list[StudyBlock]:
    result = await session.execute(
        select(StudyBlock)
        .where(StudyBlock.user_id == user_id)
        .order_by(StudyBlock.start)
    )
    return list(result.scalars().all())


async def generate_new_plan(
    session: AsyncSession,
    user_id: int,
    reason: str = "manual_replan",
) -> tuple[list[ScheduledBlock], PlanDiffResponse]:
    """Generate a new plan and return blocks + diff (not yet persisted)."""
    # Get active tasks
    result = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.status == "active")
    )
    tasks = list(result.scalars().all())

    # Get availability and rules
    grid = await get_availability_grid(session, user_id)
    rules = await get_scheduling_rules(session, user_id)

    # Get pinned blocks
    pinned_result = await session.execute(
        select(StudyBlock).where(StudyBlock.user_id == user_id, StudyBlock.is_pinned == True)
    )
    pinned_db = list(pinned_result.scalars().all())
    pinned = [
        ScheduledBlock(task_id=b.task_id, start=b.start, end=b.end, block_index=b.block_index)
        for b in pinned_db
    ]

    # Generate new plan
    new_blocks = generate_plan(tasks, grid, rules, pinned_blocks=pinned)

    # Compute diff
    old_blocks = await get_current_blocks(session, user_id)
    titles = await get_task_titles(session, user_id)
    diff = compute_diff(old_blocks, new_blocks, task_titles=titles)

    return new_blocks, diff


async def confirm_plan(
    session: AsyncSession,
    user_id: int,
    new_blocks: list[ScheduledBlock],
    reason: str = "manual_replan",
) -> int:
    """Persist a new plan, replacing old blocks. Returns plan version id."""
    # Create plan version (snapshots current state before replacing)
    old_blocks = await get_current_blocks(session, user_id)
    titles = await get_task_titles(session, user_id)
    diff = compute_diff(old_blocks, new_blocks, task_titles=titles)
    summary = f"Added {diff.added}, moved {diff.moved}, deleted {diff.deleted} blocks"

    version = await create_plan_version(session, user_id, trigger=reason, diff_summary=summary)

    # Delete old non-pinned blocks
    for block in old_blocks:
        if not block.is_pinned:
            await session.delete(block)

    # Insert new blocks
    for nb in new_blocks:
        # Skip pinned blocks (already exist)
        is_existing_pinned = any(
            b.task_id == nb.task_id and b.start == nb.start and b.is_pinned
            for b in old_blocks
        )
        if is_existing_pinned:
            continue

        block = StudyBlock(
            user_id=user_id,
            task_id=nb.task_id,
            plan_version_id=version.id,
            start=nb.start,
            end=nb.end,
            block_index=nb.block_index,
        )
        session.add(block)

    await session.commit()
    return version.id


async def move_block(
    session: AsyncSession,
    user_id: int,
    block_id: int,
    new_start: datetime,
    new_end: datetime,
) -> StudyBlock | None:
    """Move a block (user drag), pin it, and trigger replan."""
    result = await session.execute(
        select(StudyBlock).where(StudyBlock.id == block_id, StudyBlock.user_id == user_id)
    )
    block = result.scalar_one_or_none()
    if not block:
        return None

    block.start = new_start
    block.end = new_end
    block.is_pinned = True
    block.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(block)
    return block
