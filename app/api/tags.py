from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DbSession
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services import tag_service

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.post("", response_model=TagResponse, status_code=201)
async def create(data: TagCreate, user: CurrentUser, session: DbSession):
    return await tag_service.create_tag(session, user.id, data)


@router.get("", response_model=list[TagResponse])
async def list_tags(user: CurrentUser, session: DbSession):
    return await tag_service.list_tags(session, user.id)


@router.get("/{tag_id}", response_model=TagResponse)
async def get(tag_id: int, user: CurrentUser, session: DbSession):
    tag = await tag_service.get_tag(session, user.id, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update(tag_id: int, data: TagUpdate, user: CurrentUser, session: DbSession):
    tag = await tag_service.update_tag(session, user.id, tag_id, data)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete(tag_id: int, user: CurrentUser, session: DbSession):
    deleted = await tag_service.delete_tag(session, user.id, tag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found")
