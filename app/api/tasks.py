from fastapi import APIRouter, HTTPException, Query

from app.core.deps import CurrentUser, DbSession
from app.schemas.pagination import PaginatedTaskResponse
from app.schemas.task import AddTimeRequest, TaskCreate, TaskResponse, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _to_response(task, tag_ids: list[int] | None = None) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        course_id=task.course_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        difficulty=task.difficulty,
        priority=task.priority,
        task_type=task.task_type,
        focus_load=task.focus_load,
        status=task.status,
        splittable=task.splittable,
        min_block_minutes=task.min_block_minutes,
        max_block_minutes=task.max_block_minutes,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        tag_ids=tag_ids or [],
    )


@router.post("", response_model=TaskResponse, status_code=201)
async def create(data: TaskCreate, user: CurrentUser, session: DbSession):
    task = await task_service.create_task(session, user.id, data)
    return _to_response(task, data.tag_ids)


@router.get("", response_model=PaginatedTaskResponse)
async def list_tasks(
    user: CurrentUser,
    session: DbSession,
    status: str | None = Query(None),
    course_id: int | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    tasks, total = await task_service.list_tasks(
        session, user.id, status=status, course_id=course_id, offset=offset, limit=limit
    )
    task_ids = [t.id for t in tasks]
    tag_map = await task_service.get_task_tag_ids_batch(session, task_ids)
    return PaginatedTaskResponse(
        items=[_to_response(t, tag_map.get(t.id, [])) for t in tasks],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get(task_id: int, user: CurrentUser, session: DbSession):
    task = await task_service.get_task(session, user.id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tag_ids = await task_service.get_task_tag_ids(session, task_id)
    return _to_response(task, tag_ids)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update(task_id: int, data: TaskUpdate, user: CurrentUser, session: DbSession):
    task = await task_service.update_task(session, user.id, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tag_ids = await task_service.get_task_tag_ids(session, task_id)
    return _to_response(task, tag_ids)


@router.delete("/{task_id}", status_code=204)
async def delete(task_id: int, user: CurrentUser, session: DbSession):
    deleted = await task_service.delete_task(session, user.id, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete(task_id: int, user: CurrentUser, session: DbSession):
    task = await task_service.complete_task(session, user.id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tag_ids = await task_service.get_task_tag_ids(session, task_id)
    return _to_response(task, tag_ids)


@router.post("/{task_id}/add-time", response_model=TaskResponse)
async def add_time(task_id: int, data: AddTimeRequest, user: CurrentUser, session: DbSession):
    task = await task_service.add_time_to_task(session, user.id, task_id, data.additional_hours)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tag_ids = await task_service.get_task_tag_ids(session, task_id)
    return _to_response(task, tag_ids)
