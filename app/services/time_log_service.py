from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.time_log import LogType, TimeLog
from app.schemas.time_log import TimeLogCreate


async def start_focus_timer(
    session: AsyncSession,
    user_id: int,
    task_id: int,
    study_block_id: int | None = None,
) -> TimeLog:
    log = TimeLog(
        user_id=user_id,
        task_id=task_id,
        study_block_id=study_block_id,
        log_type=LogType.TIMER,
        start=datetime.now(UTC),
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def stop_focus_timer(
    session: AsyncSession,
    user_id: int,
    time_log_id: int,
) -> TimeLog | None:
    result = await session.execute(
        select(TimeLog).where(TimeLog.id == time_log_id, TimeLog.user_id == user_id)
    )
    log = result.scalar_one_or_none()
    if not log or log.end is not None:
        return None

    log.end = datetime.now(UTC)
    log.duration_minutes = (log.end - log.start).total_seconds() / 60
    await session.commit()
    await session.refresh(log)
    return log


async def create_manual_log(
    session: AsyncSession,
    user_id: int,
    data: TimeLogCreate,
) -> TimeLog:
    duration = data.duration_minutes
    if data.end and duration == 0:
        duration = (data.end - data.start).total_seconds() / 60

    log = TimeLog(
        user_id=user_id,
        task_id=data.task_id,
        study_block_id=data.study_block_id,
        log_type=LogType.MANUAL,
        start=data.start,
        end=data.end,
        duration_minutes=duration,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def list_time_logs(
    session: AsyncSession,
    user_id: int,
    task_id: int | None = None,
    limit: int = 50,
) -> list[TimeLog]:
    query = select(TimeLog).where(TimeLog.user_id == user_id)
    if task_id:
        query = query.where(TimeLog.task_id == task_id)
    query = query.order_by(TimeLog.created_at.desc()).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_total_logged_minutes(
    session: AsyncSession,
    user_id: int,
    task_id: int,
) -> float:
    result = await session.execute(
        select(TimeLog).where(TimeLog.user_id == user_id, TimeLog.task_id == task_id)
    )
    logs = result.scalars().all()
    return sum(l.duration_minutes for l in logs)
