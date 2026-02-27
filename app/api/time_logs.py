from fastapi import APIRouter, HTTPException, Query

from app.core.deps import CurrentUser, DbSession
from app.schemas.time_log import (
    FocusTimerStart,
    FocusTimerStop,
    TimeLogCreate,
    TimeLogResponse,
)
from app.services import time_log_service

router = APIRouter(prefix="/api/time-logs", tags=["time-logs"])


@router.post("/timer/start", response_model=TimeLogResponse, status_code=201)
async def start_timer(data: FocusTimerStart, user: CurrentUser, session: DbSession):
    log = await time_log_service.start_focus_timer(
        session, user.id, data.task_id, data.study_block_id
    )
    return log


@router.post("/timer/stop", response_model=TimeLogResponse)
async def stop_timer(data: FocusTimerStop, user: CurrentUser, session: DbSession):
    log = await time_log_service.stop_focus_timer(session, user.id, data.time_log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Active timer not found")
    return log


@router.post("", response_model=TimeLogResponse, status_code=201)
async def create_manual(data: TimeLogCreate, user: CurrentUser, session: DbSession):
    return await time_log_service.create_manual_log(session, user.id, data)


@router.get("", response_model=list[TimeLogResponse])
async def list_logs(
    user: CurrentUser,
    session: DbSession,
    task_id: int | None = Query(None),
):
    return await time_log_service.list_time_logs(session, user.id, task_id=task_id)


@router.get("/total/{task_id}")
async def get_total(task_id: int, user: CurrentUser, session: DbSession):
    minutes = await time_log_service.get_total_logged_minutes(session, user.id, task_id)
    return {"task_id": task_id, "total_minutes": round(minutes, 1), "total_hours": round(minutes / 60, 2)}
