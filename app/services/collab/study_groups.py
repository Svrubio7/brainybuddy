"""
Study groups service.

Provides group creation, membership management, and mutual free-time
discovery so study partners can find overlapping availability.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, select

from app.models.user import User
from app.services.collab.free_time import FreeSlot, find_mutual_free_slots


# ── SQLModel tables (not migrated yet — define as classes) ───────────


class StudyGroup(SQLModel, table=True):
    __tablename__ = "study_groups"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    owner_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StudyGroupMember(SQLModel, table=True):
    __tablename__ = "study_group_members"

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="study_groups.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Request / response schemas ───────────────────────────────────────


class GroupCreate(BaseModel):
    name: str
    description: str = ""


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    member_count: int
    created_at: datetime


class MemberAdd(BaseModel):
    user_email: str


class MemberResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    display_name: str
    email: str
    joined_at: datetime


# ── Service functions ────────────────────────────────────────────────


async def create_group(
    session: AsyncSession,
    owner_id: int,
    data: GroupCreate,
) -> StudyGroup:
    """Create a study group and add the owner as the first member."""
    group = StudyGroup(
        name=data.name,
        description=data.description,
        owner_id=owner_id,
    )
    session.add(group)
    await session.flush()  # Get the group ID

    # Owner is automatically a member
    member = StudyGroupMember(group_id=group.id, user_id=owner_id)
    session.add(member)

    await session.commit()
    await session.refresh(group)
    return group


async def add_member(
    session: AsyncSession,
    group_id: int,
    requester_id: int,
    data: MemberAdd,
) -> StudyGroupMember:
    """Add a member to a study group by email. Only group owner or existing member can add."""
    # Verify the group exists
    group_result = await session.execute(
        select(StudyGroup).where(StudyGroup.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify the requester is a member of the group
    member_check = await session.execute(
        select(StudyGroupMember).where(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id == requester_id,
        )
    )
    if member_check.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group members can add new members",
        )

    # Find the user to add
    user_result = await session.execute(
        select(User).where(User.email == data.user_email)
    )
    target_user = user_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    existing = await session.execute(
        select(StudyGroupMember).where(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id == target_user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group",
        )

    member = StudyGroupMember(group_id=group_id, user_id=target_user.id)
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


async def remove_member(
    session: AsyncSession,
    group_id: int,
    requester_id: int,
    target_user_id: int,
) -> bool:
    """
    Remove a member from a group.

    Only the group owner or the member themselves can remove.
    """
    group_result = await session.execute(
        select(StudyGroup).where(StudyGroup.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Only the owner or the user themselves can remove
    if requester_id != group.owner_id and requester_id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner or the member themselves can remove",
        )

    # Cannot remove the owner
    if target_user_id == group.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the group owner. Delete the group instead.",
        )

    member_result = await session.execute(
        select(StudyGroupMember).where(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id == target_user_id,
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        return False

    await session.delete(member)
    await session.commit()
    return True


async def list_groups(
    session: AsyncSession,
    user_id: int,
) -> list[GroupResponse]:
    """List all groups the user belongs to."""
    # Find group IDs the user is a member of
    membership_result = await session.execute(
        select(StudyGroupMember.group_id).where(
            StudyGroupMember.user_id == user_id
        )
    )
    group_ids = [row[0] for row in membership_result.all()]

    if not group_ids:
        return []

    # Load groups
    groups_result = await session.execute(
        select(StudyGroup).where(StudyGroup.id.in_(group_ids))  # type: ignore[attr-defined]
    )
    groups = list(groups_result.scalars().all())

    # Count members per group
    responses: list[GroupResponse] = []
    for g in groups:
        count_result = await session.execute(
            select(StudyGroupMember).where(StudyGroupMember.group_id == g.id)
        )
        member_count = len(list(count_result.scalars().all()))
        responses.append(
            GroupResponse(
                id=g.id,
                name=g.name,
                description=g.description,
                owner_id=g.owner_id,
                member_count=member_count,
                created_at=g.created_at,
            )
        )

    return responses


async def find_mutual_free_time(
    session: AsyncSession,
    group_id: int,
    requester_id: int,
) -> list[FreeSlot]:
    """
    Find mutual free time for all members of a study group.

    Returns overlapping availability slots that work for everyone.
    """
    # Verify the requester is a member
    member_check = await session.execute(
        select(StudyGroupMember).where(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id == requester_id,
        )
    )
    if member_check.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group members can view mutual free time",
        )

    # Get all member user IDs
    members_result = await session.execute(
        select(StudyGroupMember.user_id).where(
            StudyGroupMember.group_id == group_id
        )
    )
    user_ids = [row[0] for row in members_result.all()]

    if len(user_ids) < 2:
        return []

    return await find_mutual_free_slots(user_ids, session)
