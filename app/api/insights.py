from datetime import date

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.services import estimation_learning, insights_service

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/weekly")
async def get_weekly_insight(
    user: CurrentUser,
    session: DbSession,
    week_start: date = Query(default=None),
):
    if not week_start:
        from datetime import datetime
        today = datetime.utcnow().date()
        # Monday of current week
        week_start = today - __import__("datetime").timedelta(days=today.weekday())

    return await insights_service.compute_weekly_insight(session, user.id, week_start)


@router.get("/risk-scores")
async def get_risk_scores(user: CurrentUser, session: DbSession):
    return await insights_service.compute_risk_scores(session, user.id)


@router.get("/load-curve")
async def get_load_curve(
    user: CurrentUser,
    session: DbSession,
    days: int = Query(default=14, ge=1, le=60),
):
    return await insights_service.compute_load_curve(session, user.id, days_ahead=days)


@router.get("/multipliers")
async def get_multipliers(user: CurrentUser, session: DbSession):
    return await estimation_learning.get_all_multipliers(session, user.id)


@router.post("/multipliers/refresh/{course_id}")
async def refresh_course_multiplier(course_id: int, user: CurrentUser, session: DbSession):
    mult = await estimation_learning.update_course_multiplier(session, user.id, course_id)
    return {"course_id": course_id, "multiplier": round(mult, 2)}
