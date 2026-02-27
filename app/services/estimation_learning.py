"""
Estimation learning: track actual vs estimated hours per course+type.
Updates multipliers so future estimates improve over time.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.course import Course
from app.models.task import Task, TaskStatus
from app.models.time_log import TimeLog


async def compute_multiplier(
    session: AsyncSession,
    user_id: int,
    course_id: int | None = None,
    task_type: str | None = None,
) -> tuple[float, int]:
    """
    Compute estimation multiplier for a course+type combination.
    Returns (multiplier, sample_count).
    multiplier = avg(actual_hours / estimated_hours)
    """
    query = (
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.status == TaskStatus.COMPLETED,
            Task.estimated_hours.is_not(None),
            Task.estimated_hours > 0,
        )
    )
    if course_id:
        query = query.where(Task.course_id == course_id)
    if task_type:
        query = query.where(Task.task_type == task_type)

    result = await session.execute(query)
    tasks = result.scalars().all()

    if not tasks:
        return 1.0, 0

    ratios = []
    for task in tasks:
        log_result = await session.execute(
            select(TimeLog).where(TimeLog.task_id == task.id, TimeLog.user_id == user_id)
        )
        logs = log_result.scalars().all()
        actual_minutes = sum(l.duration_minutes for l in logs)
        actual_hours = actual_minutes / 60

        if actual_hours > 0 and task.estimated_hours:
            ratios.append(actual_hours / task.estimated_hours)

    if not ratios:
        return 1.0, 0

    multiplier = sum(ratios) / len(ratios)
    # Clamp between 0.5 and 3.0
    multiplier = max(0.5, min(3.0, multiplier))
    return multiplier, len(ratios)


async def get_all_multipliers(
    session: AsyncSession,
    user_id: int,
) -> list[dict]:
    """Get multipliers for all course+type combinations the user has data for."""
    # Get distinct course_id + task_type combos from completed tasks
    completed = await session.execute(
        select(Task.course_id, Task.task_type)
        .where(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED)
        .distinct()
    )

    results = []
    for course_id, task_type in completed.all():
        mult, count = await compute_multiplier(session, user_id, course_id, task_type)
        if count > 0:
            results.append({
                "course_id": course_id,
                "task_type": task_type,
                "multiplier": round(mult, 2),
                "sample_count": count,
            })

    return results


async def update_course_multiplier(
    session: AsyncSession,
    user_id: int,
    course_id: int,
) -> float:
    """Recompute and persist the estimation multiplier for a course."""
    mult, count = await compute_multiplier(session, user_id, course_id)
    if count > 0:
        result = await session.execute(
            select(Course).where(Course.id == course_id, Course.user_id == user_id)
        )
        course = result.scalar_one_or_none()
        if course:
            course.estimation_multiplier = mult
            await session.commit()
    return mult
