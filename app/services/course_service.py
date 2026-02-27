from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate


async def create_course(session: AsyncSession, user_id: int, data: CourseCreate) -> Course:
    course = Course(user_id=user_id, **data.model_dump())
    session.add(course)
    await session.commit()
    await session.refresh(course)
    return course


async def list_courses(session: AsyncSession, user_id: int) -> list[Course]:
    result = await session.execute(
        select(Course).where(Course.user_id == user_id).order_by(Course.name)
    )
    return list(result.scalars().all())


async def get_course(session: AsyncSession, user_id: int, course_id: int) -> Course | None:
    result = await session.execute(
        select(Course).where(Course.id == course_id, Course.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_course(
    session: AsyncSession, user_id: int, course_id: int, data: CourseUpdate
) -> Course | None:
    course = await get_course(session, user_id, course_id)
    if not course:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    course.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(course)
    return course


async def delete_course(session: AsyncSession, user_id: int, course_id: int) -> bool:
    course = await get_course(session, user_id, course_id)
    if not course:
        return False
    await session.delete(course)
    await session.commit()
    return True
