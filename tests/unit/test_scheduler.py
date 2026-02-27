from datetime import datetime, timedelta, UTC

import pytest

from app.models.task import Task
from app.schemas.availability import AvailabilityGridSchema, SchedulingRulesSchema
from app.services.scheduler.engine import generate_plan


def _make_task(task_id: int, title: str, hours: float, due_days: int, difficulty: int = 3) -> Task:
    """Create a mock task for testing."""
    t = Task(
        title=title,
        due_date=datetime.now(UTC) + timedelta(days=due_days),
        estimated_hours=hours,
        difficulty=difficulty,
        user_id=1,
        status="active",
    )
    # Manually set id for testing
    t.id = task_id
    return t


def _make_available_grid() -> AvailabilityGridSchema:
    """Create a grid that's available 8am-10pm every day."""
    available_slots = [False] * 96
    for slot in range(32, 88):  # 8:00 to 22:00
        available_slots[slot] = True
    return AvailabilityGridSchema(
        monday=available_slots[:],
        tuesday=available_slots[:],
        wednesday=available_slots[:],
        thursday=available_slots[:],
        friday=available_slots[:],
        saturday=available_slots[:],
        sunday=available_slots[:],
    )


def test_generate_plan_empty():
    grid = _make_available_grid()
    rules = SchedulingRulesSchema()
    blocks = generate_plan([], grid, rules)
    assert blocks == []


def test_generate_plan_single_task():
    tasks = [_make_task(1, "Lab Report", 2.0, 7)]
    grid = _make_available_grid()
    rules = SchedulingRulesSchema()
    blocks = generate_plan(tasks, grid, rules)
    assert len(blocks) > 0
    assert all(b.task_id == 1 for b in blocks)


def test_generate_plan_respects_difficulty_buffer():
    easy = [_make_task(1, "Easy Task", 2.0, 7, difficulty=1)]
    hard = [_make_task(2, "Hard Task", 2.0, 7, difficulty=5)]
    grid = _make_available_grid()
    rules = SchedulingRulesSchema()

    easy_blocks = generate_plan(easy, grid, rules)
    hard_blocks = generate_plan(hard, grid, rules)

    # Hard task gets more total time due to difficulty buffer
    easy_minutes = sum((b.end - b.start).total_seconds() / 60 for b in easy_blocks)
    hard_minutes = sum((b.end - b.start).total_seconds() / 60 for b in hard_blocks)
    assert hard_minutes > easy_minutes


def test_generate_plan_multiple_tasks_ordered():
    tasks = [
        _make_task(1, "Later task", 1.0, 14),
        _make_task(2, "Urgent task", 1.0, 3, difficulty=3),
    ]
    grid = _make_available_grid()
    rules = SchedulingRulesSchema()
    blocks = generate_plan(tasks, grid, rules)

    # Should have blocks for both tasks
    task_ids = {b.task_id for b in blocks}
    assert 1 in task_ids
    assert 2 in task_ids

    # Urgent task blocks should come first
    urgent_blocks = [b for b in blocks if b.task_id == 2]
    later_blocks = [b for b in blocks if b.task_id == 1]
    if urgent_blocks and later_blocks:
        assert urgent_blocks[0].start <= later_blocks[0].start


def test_generate_plan_no_availability():
    tasks = [_make_task(1, "Task", 2.0, 7)]
    grid = AvailabilityGridSchema()  # All False
    rules = SchedulingRulesSchema()
    blocks = generate_plan(tasks, grid, rules)
    assert len(blocks) == 0
