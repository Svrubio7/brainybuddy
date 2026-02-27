from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.core.deps import CurrentUser, DbSession
from app.schemas.schedule import (
    GeneratePlanRequest,
    MoveBlockRequest,
    PlanDiffResponse,
    PlanVersionResponse,
    StudyBlockResponse,
)
from app.services import schedule_service
from app.services.plan_versioning import list_plan_versions, rollback_to_version

router = APIRouter(prefix="/api/schedule", tags=["schedule"])

# Temporary storage for previewed plans (in production, use Redis)
_preview_cache: dict[int, list] = {}


@router.post("/generate", response_model=PlanDiffResponse)
async def generate_plan(data: GeneratePlanRequest, user: CurrentUser, session: DbSession):
    new_blocks, diff = await schedule_service.generate_new_plan(
        session, user.id, reason=data.reason
    )
    _preview_cache[user.id] = new_blocks
    return diff


@router.post("/confirm", response_model=dict)
async def confirm_plan(user: CurrentUser, session: DbSession):
    new_blocks = _preview_cache.pop(user.id, None)
    if new_blocks is None:
        raise HTTPException(status_code=400, detail="No plan preview to confirm")
    version_id = await schedule_service.confirm_plan(session, user.id, new_blocks)
    return {"message": "Plan confirmed", "plan_version_id": version_id}


@router.get("/blocks", response_model=list[StudyBlockResponse])
async def get_blocks(
    user: CurrentUser,
    session: DbSession,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
):
    blocks = await schedule_service.get_current_blocks(session, user.id)
    titles = await schedule_service.get_task_titles(session, user.id)

    result = []
    for b in blocks:
        if start and b.start < start:
            continue
        if end and b.end > end:
            continue
        result.append(StudyBlockResponse(
            id=b.id,
            user_id=b.user_id,
            task_id=b.task_id,
            plan_version_id=b.plan_version_id,
            start=b.start,
            end=b.end,
            block_index=b.block_index,
            is_pinned=b.is_pinned,
            created_at=b.created_at,
            task_title=titles.get(b.task_id, ""),
        ))
    return result


@router.patch("/blocks/{block_id}", response_model=StudyBlockResponse)
async def move_block(block_id: int, data: MoveBlockRequest, user: CurrentUser, session: DbSession):
    block = await schedule_service.move_block(session, user.id, block_id, data.start, data.end)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    titles = await schedule_service.get_task_titles(session, user.id)
    return StudyBlockResponse(
        id=block.id,
        user_id=block.user_id,
        task_id=block.task_id,
        plan_version_id=block.plan_version_id,
        start=block.start,
        end=block.end,
        block_index=block.block_index,
        is_pinned=block.is_pinned,
        created_at=block.created_at,
        task_title=titles.get(block.task_id, ""),
    )


@router.get("/versions", response_model=list[PlanVersionResponse])
async def get_versions(user: CurrentUser, session: DbSession):
    versions = await list_plan_versions(session, user.id)
    return [
        PlanVersionResponse(
            id=v.id,
            version_number=v.version_number,
            trigger=v.trigger,
            diff_summary=v.diff_summary,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post("/rollback/{version_id}", response_model=dict)
async def rollback(version_id: int, user: CurrentUser, session: DbSession):
    try:
        version = await rollback_to_version(session, user.id, version_id)
        await session.commit()
        return {
            "message": f"Rolled back to version {version.version_number}",
            "plan_version_id": version.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
