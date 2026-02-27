"""Collaboration API routes — sharing rules, study groups, and free time."""

from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DbSession
from app.services.collab.free_time import FreeSlot
from app.services.collab.sharing import (
    SharedBlockResponse,
    SharingRuleCreate,
    SharingRuleResponse,
    create_sharing_rule,
    delete_sharing_rule,
    get_shared_schedule,
    list_my_sharing_rules,
    list_shared_with_me,
    _rule_to_response,
)
from app.services.collab.study_groups import (
    GroupCreate,
    GroupResponse,
    MemberAdd,
    MemberResponse,
    add_member as add_group_member,
    create_group,
    find_mutual_free_time,
    list_groups,
    StudyGroupMember,
)
from app.models.user import User
from sqlmodel import select

router = APIRouter(tags=["collaboration"])


# ── Sharing rules ────────────────────────────────────────────────────


@router.post("/api/sharing", response_model=SharingRuleResponse, status_code=201)
async def create_sharing(
    data: SharingRuleCreate,
    user: CurrentUser,
    session: DbSession,
):
    """Create a new sharing rule."""
    rule = await create_sharing_rule(session, user.id, data)
    return _rule_to_response(rule)


@router.get("/api/sharing", response_model=list[SharingRuleResponse])
async def list_sharing_rules(user: CurrentUser, session: DbSession):
    """List sharing rules created by the current user."""
    rules = await list_my_sharing_rules(session, user.id)
    return [_rule_to_response(r) for r in rules]


@router.get("/api/sharing/shared-with-me", response_model=list[SharingRuleResponse])
async def list_shared_with_me_endpoint(user: CurrentUser, session: DbSession):
    """List sharing rules where others have shared their schedule with you."""
    rules = await list_shared_with_me(session, user.id)
    return [_rule_to_response(r) for r in rules]


@router.get(
    "/api/sharing/{rule_id}/schedule",
    response_model=list[SharedBlockResponse],
)
async def view_shared_schedule(
    rule_id: int,
    user: CurrentUser,
    session: DbSession,
):
    """View the schedule shared via a specific rule."""
    return await get_shared_schedule(session, rule_id, user.id)


@router.delete("/api/sharing/{rule_id}", status_code=204)
async def delete_sharing(
    rule_id: int,
    user: CurrentUser,
    session: DbSession,
):
    """Deactivate a sharing rule. Only the owner can do this."""
    deleted = await delete_sharing_rule(session, user.id, rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sharing rule not found")


# ── Study groups ─────────────────────────────────────────────────────


@router.post("/api/groups", response_model=GroupResponse, status_code=201)
async def create_study_group(
    data: GroupCreate,
    user: CurrentUser,
    session: DbSession,
):
    """Create a new study group. The creator is added as the first member."""
    group = await create_group(session, user.id, data)
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        member_count=1,
        created_at=group.created_at,
    )


@router.get("/api/groups", response_model=list[GroupResponse])
async def list_study_groups(user: CurrentUser, session: DbSession):
    """List all study groups the current user belongs to."""
    return await list_groups(session, user.id)


@router.post("/api/groups/{group_id}/members", response_model=MemberResponse, status_code=201)
async def add_member_to_group(
    group_id: int,
    data: MemberAdd,
    user: CurrentUser,
    session: DbSession,
):
    """Add a member to a study group by email."""
    member = await add_group_member(session, group_id, user.id, data)

    # Fetch the added user's details for the response
    user_result = await session.execute(
        select(User).where(User.id == member.user_id)
    )
    added_user = user_result.scalar_one_or_none()

    return MemberResponse(
        id=member.id,
        group_id=member.group_id,
        user_id=member.user_id,
        display_name=added_user.display_name if added_user else "",
        email=added_user.email if added_user else "",
        joined_at=member.joined_at,
    )


@router.get("/api/groups/{group_id}/free-time", response_model=list[FreeSlot])
async def get_group_free_time(
    group_id: int,
    user: CurrentUser,
    session: DbSession,
):
    """Find mutual free time for all members of a study group."""
    return await find_mutual_free_time(session, group_id, user.id)
