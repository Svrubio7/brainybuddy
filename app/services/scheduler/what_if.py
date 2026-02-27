"""
What-if simulator for the scheduling engine.

Allows users to preview how their plan would change under hypothetical
scenarios *without* persisting anything to the database.

Supported scenario types:
  - add_commitment   : Block out a range of hours (e.g. new part-time job)
  - remove_hours     : Reduce daily available hours for a date range
  - add_task         : Add a hypothetical new task
  - change_deadline  : Move the deadline of an existing task
"""

from __future__ import annotations

import enum
from datetime import UTC, date, datetime, timedelta

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.study_block import StudyBlock
from app.models.task import Task
from app.schemas.schedule import PlanDiffResponse
from app.services.availability_service import get_availability_grid, get_scheduling_rules
from app.services.scheduler.diff import compute_diff
from app.services.scheduler.engine import ScheduledBlock, generate_plan


class ScenarioType(str, enum.Enum):
    ADD_COMMITMENT = "add_commitment"
    REMOVE_HOURS = "remove_hours"
    ADD_TASK = "add_task"
    CHANGE_DEADLINE = "change_deadline"


class Scenario(BaseModel):
    """A hypothetical change to explore."""

    scenario_type: ScenarioType

    # add_commitment: block out specific hours on specific days of the week
    commitment_days: list[int] | None = Field(
        default=None,
        description="Days of the week (0=Monday..6=Sunday) affected",
    )
    commitment_start_hour: int | None = None
    commitment_end_hour: int | None = None

    # remove_hours: reduce daily cap for a date range
    reduce_hours_by: float | None = Field(
        default=None, description="Hours to subtract from daily cap",
    )
    date_range_start: date | None = None
    date_range_end: date | None = None

    # add_task: hypothetical task details
    task_title: str | None = None
    task_estimated_hours: float | None = None
    task_due_date: datetime | None = None
    task_focus_load: str | None = None
    task_difficulty: int | None = None
    task_course_id: int | None = None

    # change_deadline: existing task id + new deadline
    target_task_id: int | None = None
    new_deadline: datetime | None = None


class SimulationResult(BaseModel):
    """Result of a what-if simulation."""

    scenario: Scenario
    diff: PlanDiffResponse
    warnings: list[str] = []


async def simulate_scenario(
    session: AsyncSession,
    user_id: int,
    scenario: Scenario,
) -> SimulationResult:
    """
    Run a what-if simulation and return a PlanDiff without persisting.

    The function loads the user's real tasks, availability, and rules,
    applies the hypothetical scenario, runs the planner, and computes
    the diff against the current plan.
    """
    # Load real data
    task_result = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.status == "active")
    )
    tasks = list(task_result.scalars().all())

    grid = await get_availability_grid(session, user_id)
    rules = await get_scheduling_rules(session, user_id)

    # Load current blocks for diff
    block_result = await session.execute(
        select(StudyBlock)
        .where(StudyBlock.user_id == user_id)
        .order_by(StudyBlock.start)
    )
    current_blocks = list(block_result.scalars().all())

    # Build task title map
    titles: dict[int, str] = {t.id: t.title for t in tasks}

    warnings: list[str] = []

    # ── Apply scenario mutations (on copies, never on DB objects) ──

    if scenario.scenario_type == ScenarioType.ADD_COMMITMENT:
        grid = _apply_commitment(grid, scenario)

    elif scenario.scenario_type == ScenarioType.REMOVE_HOURS:
        rules_dict = rules.model_dump()
        reduce_by = scenario.reduce_hours_by or 0.0
        new_daily = max(0.0, rules_dict["daily_max_hours"] - reduce_by)
        new_weekend = max(0.0, rules_dict["weekend_max_hours"] - reduce_by)
        if new_daily <= 0:
            warnings.append(
                "Reducing hours leaves zero daily capacity — plan will be empty."
            )
        rules_dict["daily_max_hours"] = new_daily
        rules_dict["weekend_max_hours"] = new_weekend
        rules = type(rules)(**rules_dict)

    elif scenario.scenario_type == ScenarioType.ADD_TASK:
        hypothetical_task = _build_hypothetical_task(user_id, scenario, tasks)
        tasks = list(tasks) + [hypothetical_task]
        titles[hypothetical_task.id] = hypothetical_task.title

    elif scenario.scenario_type == ScenarioType.CHANGE_DEADLINE:
        tasks = _apply_deadline_change(tasks, scenario, warnings)

    # Get pinned blocks
    pinned_result = await session.execute(
        select(StudyBlock).where(
            StudyBlock.user_id == user_id, StudyBlock.is_pinned == True  # noqa: E712
        )
    )
    pinned_db = list(pinned_result.scalars().all())
    pinned = [
        ScheduledBlock(
            task_id=b.task_id, start=b.start, end=b.end, block_index=b.block_index
        )
        for b in pinned_db
    ]

    # Run the planner with the modified inputs
    new_blocks = generate_plan(tasks, grid, rules, pinned_blocks=pinned)

    # Compute diff against current persisted plan
    diff = compute_diff(current_blocks, new_blocks, task_titles=titles)

    return SimulationResult(scenario=scenario, diff=diff, warnings=warnings)


# ── Helpers ──────────────────────────────────────────────────────────


def _apply_commitment(grid, scenario: Scenario):
    """Remove availability for the committed hours on the specified days."""
    from app.schemas.availability import AvailabilityGridSchema

    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    grid_dict = grid.model_dump()

    days = scenario.commitment_days or []
    start_hour = scenario.commitment_start_hour or 0
    end_hour = scenario.commitment_end_hour or 24

    for day_idx in days:
        if 0 <= day_idx <= 6:
            day_key = day_names[day_idx]
            slots = list(grid_dict[day_key])
            for h in range(start_hour, min(end_hour, 24)):
                # Each hour has 4 x 15-min slots
                for quarter in range(4):
                    slot_idx = h * 4 + quarter
                    if slot_idx < len(slots):
                        slots[slot_idx] = False
            grid_dict[day_key] = slots

    return AvailabilityGridSchema(**grid_dict)


def _build_hypothetical_task(
    user_id: int, scenario: Scenario, existing_tasks: list[Task]
) -> Task:
    """Create a non-persisted Task object for the simulation."""
    # Use a negative id to avoid collisions with real tasks
    min_id = min((t.id for t in existing_tasks if t.id is not None), default=0)
    fake_id = min(min_id, 0) - 1

    return Task(
        id=fake_id,
        user_id=user_id,
        title=scenario.task_title or "Hypothetical Task",
        estimated_hours=scenario.task_estimated_hours or 2.0,
        due_date=scenario.task_due_date or datetime.now(UTC) + timedelta(days=14),
        focus_load=scenario.task_focus_load or "medium",
        difficulty=scenario.task_difficulty or 3,
        course_id=scenario.task_course_id,
        status="active",
    )


def _apply_deadline_change(
    tasks: list[Task], scenario: Scenario, warnings: list[str]
) -> list[Task]:
    """Return a copy of tasks with one deadline changed."""
    if scenario.target_task_id is None or scenario.new_deadline is None:
        warnings.append("change_deadline requires target_task_id and new_deadline.")
        return tasks

    modified: list[Task] = []
    found = False
    for t in tasks:
        if t.id == scenario.target_task_id:
            found = True
            # We cannot modify the ORM object directly (it's attached to a
            # session), so we create a detached copy via model_validate.
            data = {
                "id": t.id,
                "user_id": t.user_id,
                "title": t.title,
                "description": t.description,
                "due_date": scenario.new_deadline,
                "estimated_hours": t.estimated_hours,
                "difficulty": t.difficulty,
                "priority": t.priority,
                "task_type": t.task_type,
                "focus_load": t.focus_load,
                "status": t.status,
                "splittable": t.splittable,
                "min_block_minutes": t.min_block_minutes,
                "max_block_minutes": t.max_block_minutes,
                "course_id": t.course_id,
                "completed_at": t.completed_at,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            copy = Task.model_validate(data)
            modified.append(copy)
        else:
            modified.append(t)

    if not found:
        warnings.append(f"Task {scenario.target_task_id} not found among active tasks.")

    return modified
