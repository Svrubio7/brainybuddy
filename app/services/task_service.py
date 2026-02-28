from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.tag import TaskTag
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(session: AsyncSession, user_id: int, data: TaskCreate) -> Task:
    task = Task(
        user_id=user_id,
        title=data.title,
        due_date=data.due_date,
        course_id=data.course_id,
        description=data.description,
        estimated_hours=data.estimated_hours,
        difficulty=data.difficulty,
        priority=data.priority,
        task_type=data.task_type,
        focus_load=data.focus_load,
        splittable=data.splittable,
        min_block_minutes=data.min_block_minutes,
        max_block_minutes=data.max_block_minutes,
    )
    session.add(task)
    await session.flush()

    for tag_id in data.tag_ids:
        session.add(TaskTag(task_id=task.id, tag_id=tag_id))

    await session.commit()
    await session.refresh(task)
    return task


async def list_tasks(
    session: AsyncSession,
    user_id: int,
    status: str | None = None,
    course_id: int | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Task], int]:
    from sqlalchemy import func

    base = select(Task).where(Task.user_id == user_id)
    if status:
        base = base.where(Task.status == status)
    if course_id:
        base = base.where(Task.course_id == course_id)

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_q)).scalar_one()

    # Fetch page
    query = base.order_by(Task.due_date.asc()).offset(offset).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all()), total


async def get_task(session: AsyncSession, user_id: int, task_id: int) -> Task | None:
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_task(
    session: AsyncSession, user_id: int, task_id: int, data: TaskUpdate
) -> Task | None:
    task = await get_task(session, user_id, task_id)
    if not task:
        return None

    update_data = data.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()

    if tag_ids is not None:
        # Remove existing tags
        existing = await session.execute(
            select(TaskTag).where(TaskTag.task_id == task_id)
        )
        for tt in existing.scalars().all():
            await session.delete(tt)
        # Add new tags
        for tid in tag_ids:
            session.add(TaskTag(task_id=task_id, tag_id=tid))

    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, user_id: int, task_id: int) -> bool:
    task = await get_task(session, user_id, task_id)
    if not task:
        return False
    await session.delete(task)
    await session.commit()
    return True


async def complete_task(session: AsyncSession, user_id: int, task_id: int) -> Task | None:
    task = await get_task(session, user_id, task_id)
    if not task:
        return None
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(task)
    return task


async def add_time_to_task(
    session: AsyncSession, user_id: int, task_id: int, additional_hours: float
) -> Task | None:
    task = await get_task(session, user_id, task_id)
    if not task:
        return None
    current = task.estimated_hours or 0
    task.estimated_hours = current + additional_hours
    task.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(task)
    return task


async def get_task_tag_ids(session: AsyncSession, task_id: int) -> list[int]:
    result = await session.execute(select(TaskTag).where(TaskTag.task_id == task_id))
    return [tt.tag_id for tt in result.scalars().all()]


async def get_task_tag_ids_batch(
    session: AsyncSession, task_ids: list[int]
) -> dict[int, list[int]]:
    """Fetch tag IDs for multiple tasks in a single query."""
    if not task_ids:
        return {}
    result = await session.execute(select(TaskTag).where(TaskTag.task_id.in_(task_ids)))
    mapping: dict[int, list[int]] = {tid: [] for tid in task_ids}
    for tt in result.scalars().all():
        mapping[tt.task_id].append(tt.tag_id)
    return mapping
