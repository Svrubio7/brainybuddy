import json
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.plan_version import PlanVersion
from app.models.study_block import StudyBlock


async def create_plan_version(
    session: AsyncSession,
    user_id: int,
    trigger: str,
    diff_summary: str = "",
) -> PlanVersion:
    # Get current version number
    result = await session.execute(
        select(PlanVersion)
        .where(PlanVersion.user_id == user_id)
        .order_by(PlanVersion.version_number.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    next_version = (latest.version_number + 1) if latest else 1

    # Snapshot current blocks
    blocks_result = await session.execute(
        select(StudyBlock).where(StudyBlock.user_id == user_id)
    )
    blocks = blocks_result.scalars().all()
    snapshot = json.dumps(
        [
            {
                "id": b.id,
                "task_id": b.task_id,
                "start": b.start.isoformat(),
                "end": b.end.isoformat(),
                "block_index": b.block_index,
                "is_pinned": b.is_pinned,
            }
            for b in blocks
        ]
    )

    plan_version = PlanVersion(
        user_id=user_id,
        version_number=next_version,
        trigger=trigger,
        snapshot=snapshot,
        diff_summary=diff_summary,
    )
    session.add(plan_version)
    await session.flush()
    return plan_version


async def rollback_to_version(
    session: AsyncSession,
    user_id: int,
    version_id: int,
) -> PlanVersion:
    # Get target version
    result = await session.execute(
        select(PlanVersion).where(
            PlanVersion.id == version_id,
            PlanVersion.user_id == user_id,
        )
    )
    target_version = result.scalar_one_or_none()
    if target_version is None:
        raise ValueError(f"Plan version {version_id} not found")

    # Create a new version recording the rollback
    rollback_version = await create_plan_version(
        session, user_id, trigger=f"rollback_to_v{target_version.version_number}"
    )

    # Delete current blocks
    current_blocks = await session.execute(
        select(StudyBlock).where(StudyBlock.user_id == user_id)
    )
    for block in current_blocks.scalars().all():
        await session.delete(block)

    # Restore blocks from snapshot
    snapshot_blocks = json.loads(target_version.snapshot)
    for block_data in snapshot_blocks:
        block = StudyBlock(
            user_id=user_id,
            task_id=block_data["task_id"],
            plan_version_id=rollback_version.id,
            start=datetime.fromisoformat(block_data["start"]),
            end=datetime.fromisoformat(block_data["end"]),
            block_index=block_data["block_index"],
            is_pinned=block_data.get("is_pinned", False),
        )
        session.add(block)

    await session.flush()
    return rollback_version


async def list_plan_versions(
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[PlanVersion]:
    result = await session.execute(
        select(PlanVersion)
        .where(PlanVersion.user_id == user_id)
        .order_by(PlanVersion.version_number.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
