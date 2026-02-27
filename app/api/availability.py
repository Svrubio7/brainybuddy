from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.availability import AvailabilityGridSchema, SchedulingRulesSchema
from app.services import availability_service

router = APIRouter(prefix="/api", tags=["availability"])


@router.get("/availability", response_model=AvailabilityGridSchema)
async def get_availability(user: CurrentUser, session: DbSession):
    return await availability_service.get_availability_grid(session, user.id)


@router.put("/availability", response_model=AvailabilityGridSchema)
async def update_availability(
    data: AvailabilityGridSchema, user: CurrentUser, session: DbSession
):
    return await availability_service.update_availability_grid(session, user.id, data)


@router.get("/rules", response_model=SchedulingRulesSchema)
async def get_rules(user: CurrentUser, session: DbSession):
    return await availability_service.get_scheduling_rules(session, user.id)


@router.put("/rules", response_model=SchedulingRulesSchema)
async def update_rules(data: SchedulingRulesSchema, user: CurrentUser, session: DbSession):
    return await availability_service.update_scheduling_rules(session, user.id, data)
