"""
Deterministic scheduling engine.

Algorithm: Earliest-deadline-first allocation with constraint satisfaction.
- Build 15-min slot timeline from availability + external events
- Sort tasks by deadline ASC, priority DESC
- Allocate blocks earliest-first with difficulty buffer (1 + (difficulty-3)*0.1)
- Respect hard constraints (availability, no overlap, daily cap, deadline)
- Apply soft constraints (break cadence, max consecutive per subject, preferred windows)
- Minimum-viable-progress blocks when overloaded
"""

from datetime import UTC, datetime, timedelta

from app.models.task import Priority, Task
from app.schemas.availability import AvailabilityGridSchema, SchedulingRulesSchema

SLOT_MINUTES = 15
PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    "critical": 0,
    Priority.HIGH: 1,
    "high": 1,
    Priority.MEDIUM: 2,
    "medium": 2,
    Priority.LOW: 3,
    "low": 3,
}

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class ScheduledBlock:
    """A scheduled study block output from the engine."""

    def __init__(
        self,
        task_id: int,
        start: datetime,
        end: datetime,
        block_index: int = 0,
    ):
        self.task_id = task_id
        self.start = start
        self.end = end
        self.block_index = block_index


def _difficulty_multiplier(difficulty: int) -> float:
    return 1.0 + (difficulty - 3) * 0.1


def _get_slot_availability(
    dt: datetime,
    grid: AvailabilityGridSchema,
    rules: SchedulingRulesSchema,
) -> bool:
    """Check if a 15-min slot starting at dt is available."""
    day_name = DAY_NAMES[dt.weekday()]
    day_slots = getattr(grid, day_name, [])
    slot_index = (dt.hour * 60 + dt.minute) // SLOT_MINUTES
    if slot_index >= len(day_slots):
        return False
    if not day_slots[slot_index]:
        return False

    hour = dt.hour
    # Sleep protection
    if rules.sleep_start_hour > rules.sleep_end_hour:
        if hour >= rules.sleep_start_hour or hour < rules.sleep_end_hour:
            return False
    elif rules.sleep_start_hour <= hour < rules.sleep_end_hour:
        return False

    return True


def _sort_tasks(tasks: list[Task]) -> list[Task]:
    """Sort by deadline ASC, then priority DESC."""
    return sorted(
        tasks,
        key=lambda t: (t.due_date, PRIORITY_ORDER.get(t.priority, 2)),
    )


def generate_plan(
    tasks: list[Task],
    grid: AvailabilityGridSchema,
    rules: SchedulingRulesSchema,
    pinned_blocks: list[ScheduledBlock] | None = None,
    plan_start: datetime | None = None,
) -> list[ScheduledBlock]:
    """
    Generate a full study plan.

    Returns a list of ScheduledBlock objects representing the allocated time.
    """
    if not tasks:
        return []

    pinned = pinned_blocks or []
    now = plan_start or datetime.now(UTC)
    # Round up to next slot boundary
    minute_remainder = now.minute % SLOT_MINUTES
    if minute_remainder != 0:
        now = now + timedelta(minutes=SLOT_MINUTES - minute_remainder)
    now = now.replace(second=0, microsecond=0)

    sorted_tasks = _sort_tasks([t for t in tasks if t.status == "active"])
    if not sorted_tasks:
        return list(pinned)

    # Planning horizon: max(latest deadline + 14 days, now + 30 days)
    latest_deadline = max(t.due_date for t in sorted_tasks)
    horizon = max(latest_deadline + timedelta(days=14), now + timedelta(days=30))

    # Build occupied slots from pinned blocks
    occupied: set[datetime] = set()
    for b in pinned:
        slot = b.start
        while slot < b.end:
            occupied.add(slot)
            slot += timedelta(minutes=SLOT_MINUTES)

    # Track daily hours used
    daily_hours: dict[str, float] = {}
    # Track consecutive slots per subject (course_id)
    last_subject: dict[str, int | None] = {}  # date_str -> course_id

    results: list[ScheduledBlock] = list(pinned)

    for task in sorted_tasks:
        estimated = task.estimated_hours or 1.0
        multiplier = _difficulty_multiplier(task.difficulty)
        total_minutes_needed = int(estimated * multiplier * 60)

        min_block = task.min_block_minutes if task.splittable else total_minutes_needed
        max_block = task.max_block_minutes if task.splittable else total_minutes_needed

        # Ensure at least one minimum-viable-progress block
        min_progress_minutes = min(min_block, total_minutes_needed)

        minutes_allocated = 0
        block_index = 0
        slot = now

        while minutes_allocated < total_minutes_needed and slot < horizon:
            if slot >= task.due_date:
                # Past deadline, still allocate minimum viable progress
                if minutes_allocated < min_progress_minutes:
                    pass  # Continue trying
                else:
                    break

            if not _get_slot_availability(slot, grid, rules):
                slot += timedelta(minutes=SLOT_MINUTES)
                continue

            if slot in occupied:
                slot += timedelta(minutes=SLOT_MINUTES)
                continue

            # Check daily cap
            date_str = slot.strftime("%Y-%m-%d")
            is_weekend = slot.weekday() >= 5
            max_daily = (
                rules.weekend_max_hours
                if (is_weekend and rules.lighter_weekends)
                else rules.daily_max_hours
            )
            current_daily = daily_hours.get(date_str, 0.0)
            if current_daily >= max_daily:
                # Skip to next day
                next_day = (slot + timedelta(days=1)).replace(hour=0, minute=0)
                slot = next_day
                continue

            # Try to build a contiguous block
            block_slots = 0
            remaining_needed = total_minutes_needed - minutes_allocated
            target_slots = min(max_block, remaining_needed) // SLOT_MINUTES
            target_slots = max(target_slots, min_block // SLOT_MINUTES)

            check_slot = slot
            consecutive_same_subject = 0
            while block_slots < target_slots and check_slot < horizon:
                if check_slot in occupied:
                    break
                if not _get_slot_availability(check_slot, grid, rules):
                    break

                # Check daily cap for this slot
                cs_date = check_slot.strftime("%Y-%m-%d")
                cs_daily = daily_hours.get(cs_date, 0.0) + (block_slots * SLOT_MINUTES / 60)
                cs_weekend = check_slot.weekday() >= 5
                cs_max = (
                    rules.weekend_max_hours
                    if (cs_weekend and rules.lighter_weekends)
                    else rules.daily_max_hours
                )
                if cs_daily >= cs_max:
                    break

                # Check max consecutive same subject
                if task.course_id and last_subject.get(cs_date) == task.course_id:
                    consecutive_same_subject += SLOT_MINUTES
                    if consecutive_same_subject > rules.max_consecutive_same_subject_minutes:
                        break

                block_slots += 1
                check_slot += timedelta(minutes=SLOT_MINUTES)

            # Need at least enough slots for min_block
            min_slots = min_block // SLOT_MINUTES
            if block_slots < min_slots and minutes_allocated + (block_slots * SLOT_MINUTES) < total_minutes_needed:
                # Not enough contiguous slots, try next slot
                slot += timedelta(minutes=SLOT_MINUTES)
                continue

            if block_slots == 0:
                slot += timedelta(minutes=SLOT_MINUTES)
                continue

            # Allocate the block
            block_start = slot
            block_end = slot + timedelta(minutes=block_slots * SLOT_MINUTES)

            results.append(ScheduledBlock(
                task_id=task.id,
                start=block_start,
                end=block_end,
                block_index=block_index,
            ))

            # Mark slots as occupied
            mark_slot = block_start
            while mark_slot < block_end:
                occupied.add(mark_slot)
                mark_slot += timedelta(minutes=SLOT_MINUTES)

            # Update tracking
            block_minutes = block_slots * SLOT_MINUTES
            minutes_allocated += block_minutes
            daily_hours[date_str] = daily_hours.get(date_str, 0.0) + block_minutes / 60
            last_subject[date_str] = task.course_id
            block_index += 1

            # Add break after this block if needed
            if block_minutes >= rules.break_after_minutes:
                break_slots = rules.break_duration_minutes // SLOT_MINUTES
                break_slot = block_end
                for _ in range(break_slots):
                    occupied.add(break_slot)
                    break_slot += timedelta(minutes=SLOT_MINUTES)
                slot = break_slot
            else:
                slot = block_end

    return results
