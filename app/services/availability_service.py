import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.availability import AvailabilityGrid, SchedulingRules
from app.schemas.availability import AvailabilityGridSchema, SchedulingRulesSchema


async def get_availability_grid(session: AsyncSession, user_id: int) -> AvailabilityGridSchema:
    result = await session.execute(
        select(AvailabilityGrid).where(AvailabilityGrid.user_id == user_id)
    )
    grid = result.scalar_one_or_none()
    if not grid:
        return AvailabilityGridSchema()
    return AvailabilityGridSchema(**json.loads(grid.grid))


async def update_availability_grid(
    session: AsyncSession, user_id: int, data: AvailabilityGridSchema
) -> AvailabilityGridSchema:
    result = await session.execute(
        select(AvailabilityGrid).where(AvailabilityGrid.user_id == user_id)
    )
    grid = result.scalar_one_or_none()
    grid_json = json.dumps(data.model_dump())

    if grid:
        grid.grid = grid_json
    else:
        grid = AvailabilityGrid(user_id=user_id, grid=grid_json)
        session.add(grid)

    await session.commit()
    return data


async def get_scheduling_rules(session: AsyncSession, user_id: int) -> SchedulingRulesSchema:
    result = await session.execute(
        select(SchedulingRules).where(SchedulingRules.user_id == user_id)
    )
    rules = result.scalar_one_or_none()
    if not rules:
        return SchedulingRulesSchema()
    return SchedulingRulesSchema(
        daily_max_hours=rules.daily_max_hours,
        break_after_minutes=rules.break_after_minutes,
        break_duration_minutes=rules.break_duration_minutes,
        max_consecutive_same_subject_minutes=rules.max_consecutive_same_subject_minutes,
        preferred_start_hour=rules.preferred_start_hour,
        preferred_end_hour=rules.preferred_end_hour,
        slot_duration_minutes=rules.slot_duration_minutes,
        sleep_start_hour=rules.sleep_start_hour,
        sleep_end_hour=rules.sleep_end_hour,
        lighter_weekends=rules.lighter_weekends,
        weekend_max_hours=rules.weekend_max_hours,
    )


async def update_scheduling_rules(
    session: AsyncSession, user_id: int, data: SchedulingRulesSchema
) -> SchedulingRulesSchema:
    result = await session.execute(
        select(SchedulingRules).where(SchedulingRules.user_id == user_id)
    )
    rules = result.scalar_one_or_none()

    if rules:
        for key, value in data.model_dump().items():
            setattr(rules, key, value)
    else:
        rules = SchedulingRules(user_id=user_id, **data.model_dump())
        session.add(rules)

    await session.commit()
    return data
