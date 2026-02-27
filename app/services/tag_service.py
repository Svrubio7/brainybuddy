from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


async def create_tag(session: AsyncSession, user_id: int, data: TagCreate) -> Tag:
    tag = Tag(user_id=user_id, **data.model_dump())
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


async def list_tags(session: AsyncSession, user_id: int) -> list[Tag]:
    result = await session.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)
    )
    return list(result.scalars().all())


async def get_tag(session: AsyncSession, user_id: int, tag_id: int) -> Tag | None:
    result = await session.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_tag(
    session: AsyncSession, user_id: int, tag_id: int, data: TagUpdate
) -> Tag | None:
    tag = await get_tag(session, user_id, tag_id)
    if not tag:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
    await session.commit()
    await session.refresh(tag)
    return tag


async def delete_tag(session: AsyncSession, user_id: int, tag_id: int) -> bool:
    tag = await get_tag(session, user_id, tag_id)
    if not tag:
        return False
    await session.delete(tag)
    await session.commit()
    return True
