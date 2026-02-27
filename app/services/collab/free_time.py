"""
Free time finder — intersects availability grids across multiple users.

This module computes the "Venn diagram" of free slots: the time windows
where *all* specified users are available according to their
AvailabilityGrid and SchedulingRules.
"""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.availability_service import get_availability_grid, get_scheduling_rules

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
SLOTS_PER_DAY = 96  # 24 hours * 4 quarters
SLOT_MINUTES = 15


class FreeSlot(BaseModel):
    """A contiguous window of mutual availability."""

    day: str  # e.g. "monday"
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
    duration_minutes: int


async def find_mutual_free_slots(
    user_ids: list[int],
    session: AsyncSession,
    min_duration_minutes: int = 30,
) -> list[FreeSlot]:
    """
    Intersect availability grids for all given users.

    Parameters
    ----------
    user_ids : list[int]
        Users whose availability to intersect.
    session : AsyncSession
        Database session.
    min_duration_minutes : int
        Minimum contiguous free block to report (default 30 min).

    Returns
    -------
    list[FreeSlot]
        List of overlapping free slots, sorted by day then time.
    """
    if len(user_ids) < 2:
        return []

    # Load all grids and rules
    grids = []
    rules_list = []
    for uid in user_ids:
        grid = await get_availability_grid(session, uid)
        rules = await get_scheduling_rules(session, uid)
        grids.append(grid)
        rules_list.append(rules)

    # For each day, intersect the availability bitmaps
    results: list[FreeSlot] = []

    for day_name in DAY_NAMES:
        # Start with all slots True, then AND with each user's grid
        mutual: list[bool] = [True] * SLOTS_PER_DAY

        for grid, rules in zip(grids, rules_list):
            user_day_slots: list[bool] = getattr(grid, day_name, [False] * SLOTS_PER_DAY)

            for slot_idx in range(SLOTS_PER_DAY):
                if not user_day_slots[slot_idx] if slot_idx < len(user_day_slots) else True:
                    mutual[slot_idx] = False
                    continue

                # Apply sleep protection
                hour = (slot_idx * SLOT_MINUTES) // 60
                if rules.sleep_start_hour > rules.sleep_end_hour:
                    # Wraps midnight, e.g. sleep 23-7
                    if hour >= rules.sleep_start_hour or hour < rules.sleep_end_hour:
                        mutual[slot_idx] = False
                elif rules.sleep_start_hour <= hour < rules.sleep_end_hour:
                    mutual[slot_idx] = False

        # Extract contiguous free runs from the mutual array
        run_start: int | None = None
        for slot_idx in range(SLOTS_PER_DAY + 1):
            is_free = mutual[slot_idx] if slot_idx < SLOTS_PER_DAY else False

            if is_free and run_start is None:
                run_start = slot_idx
            elif not is_free and run_start is not None:
                run_length = slot_idx - run_start
                duration = run_length * SLOT_MINUTES

                if duration >= min_duration_minutes:
                    start_total_minutes = run_start * SLOT_MINUTES
                    end_total_minutes = slot_idx * SLOT_MINUTES

                    results.append(
                        FreeSlot(
                            day=day_name,
                            start_hour=start_total_minutes // 60,
                            start_minute=start_total_minutes % 60,
                            end_hour=end_total_minutes // 60,
                            end_minute=end_total_minutes % 60,
                            duration_minutes=duration,
                        )
                    )

                run_start = None

    return results
