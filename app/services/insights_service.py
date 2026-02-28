"""
Insights: planned vs actual hours, load curves, risk scores.
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.insight import Insight
from app.models.study_block import StudyBlock
from app.models.task import Task
from app.models.time_log import TimeLog


async def compute_weekly_insight(
    session: AsyncSession,
    user_id: int,
    week_start: date,
    course_id: int | None = None,
) -> dict:
    """Compute planned vs actual for a given week."""
    week_start_dt = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=UTC)
    week_end_dt = week_start_dt + timedelta(days=7)

    # Planned hours from study blocks
    blocks_query = select(StudyBlock).where(
        StudyBlock.user_id == user_id,
        StudyBlock.start >= week_start_dt,
        StudyBlock.end <= week_end_dt,
    )
    result = await session.execute(blocks_query)
    blocks = result.scalars().all()
    planned_minutes = sum(
        (b.end - b.start).total_seconds() / 60 for b in blocks
    )

    # Actual hours from time logs
    logs_query = select(TimeLog).where(
        TimeLog.user_id == user_id,
        TimeLog.start >= week_start_dt,
    )
    result = await session.execute(logs_query)
    logs = result.scalars().all()
    actual_minutes = sum(l.duration_minutes for l in logs if l.duration_minutes > 0)

    planned_hours = planned_minutes / 60
    actual_hours = actual_minutes / 60

    return {
        "week_start": week_start.isoformat(),
        "planned_hours": round(planned_hours, 1),
        "actual_hours": round(actual_hours, 1),
        "completion_rate": round(actual_hours / planned_hours, 2) if planned_hours > 0 else 0,
    }


async def compute_risk_scores(
    session: AsyncSession,
    user_id: int,
) -> list[dict]:
    """
    Risk score per active task.
    risk = 1 - (available_hours_before_deadline / remaining_hours_needed)
    Higher score = more at risk.
    """
    result = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.status == "active")
    )
    tasks = result.scalars().all()

    now = datetime.utcnow()
    risks = []

    for task in tasks:
        estimated = task.estimated_hours or 1.0

        # Get logged time
        log_result = await session.execute(
            select(TimeLog).where(TimeLog.task_id == task.id, TimeLog.user_id == user_id)
        )
        logs = log_result.scalars().all()
        logged_hours = sum(l.duration_minutes for l in logs) / 60

        remaining_hours = max(0, estimated - logged_hours)
        hours_until_due = max(0, (task.due_date - now).total_seconds() / 3600)

        # Assume ~6 productive hours per day
        available_hours = hours_until_due * (6 / 24)

        if remaining_hours <= 0:
            risk = 0.0
        elif available_hours <= 0:
            risk = 1.0
        else:
            risk = 1.0 - min(1.0, available_hours / (remaining_hours * 1.5))
            risk = max(0.0, risk)

        risks.append({
            "task_id": task.id,
            "task_title": task.title,
            "remaining_hours": round(remaining_hours, 1),
            "hours_until_due": round(hours_until_due, 1),
            "risk_score": round(risk, 2),
        })

    return sorted(risks, key=lambda r: r["risk_score"], reverse=True)


async def compute_load_curve(
    session: AsyncSession,
    user_id: int,
    days_ahead: int = 14,
) -> list[dict]:
    """Daily planned study hours for the next N days."""
    now = datetime.utcnow()
    results = []

    for i in range(days_ahead):
        day = now + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        blocks_result = await session.execute(
            select(StudyBlock).where(
                StudyBlock.user_id == user_id,
                StudyBlock.start >= day_start,
                StudyBlock.start < day_end,
            )
        )
        blocks = blocks_result.scalars().all()
        hours = sum((b.end - b.start).total_seconds() / 3600 for b in blocks)

        results.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "planned_hours": round(hours, 1),
        })

    return results


async def save_weekly_insight(
    session: AsyncSession,
    user_id: int,
    week_start: date,
    planned_hours: float,
    actual_hours: float,
    risk_score: float = 0,
    course_id: int | None = None,
) -> Insight:
    """Persist a weekly insight record."""
    # Check if already exists
    result = await session.execute(
        select(Insight).where(
            Insight.user_id == user_id,
            Insight.week_start == week_start,
            Insight.course_id == course_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.planned_hours = planned_hours
        existing.actual_hours = actual_hours
        existing.risk_score = risk_score
        await session.commit()
        return existing

    insight = Insight(
        user_id=user_id,
        course_id=course_id,
        week_start=week_start,
        planned_hours=planned_hours,
        actual_hours=actual_hours,
        risk_score=risk_score,
    )
    session.add(insight)
    await session.commit()
    await session.refresh(insight)
    return insight
