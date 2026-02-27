from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DbSession
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from app.services import course_service

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.post("", response_model=CourseResponse, status_code=201)
async def create(data: CourseCreate, user: CurrentUser, session: DbSession):
    return await course_service.create_course(session, user.id, data)


@router.get("", response_model=list[CourseResponse])
async def list_courses(user: CurrentUser, session: DbSession):
    return await course_service.list_courses(session, user.id)


@router.get("/{course_id}", response_model=CourseResponse)
async def get(course_id: int, user: CurrentUser, session: DbSession):
    course = await course_service.get_course(session, user.id, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.patch("/{course_id}", response_model=CourseResponse)
async def update(course_id: int, data: CourseUpdate, user: CurrentUser, session: DbSession):
    course = await course_service.update_course(session, user.id, course_id, data)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.delete("/{course_id}", status_code=204)
async def delete(course_id: int, user: CurrentUser, session: DbSession):
    deleted = await course_service.delete_course(session, user.id, course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
