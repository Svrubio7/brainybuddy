"""Compute diff between two sets of study blocks."""

from app.models.study_block import StudyBlock
from app.schemas.schedule import PlanDiffItem, PlanDiffResponse


def compute_diff(
    old_blocks: list[StudyBlock],
    new_blocks: list,  # ScheduledBlock from engine
    task_titles: dict[int, str] | None = None,
) -> PlanDiffResponse:
    titles = task_titles or {}
    old_by_task: dict[int, list[StudyBlock]] = {}
    for b in old_blocks:
        old_by_task.setdefault(b.task_id, []).append(b)

    new_by_task: dict[int, list] = {}
    for b in new_blocks:
        new_by_task.setdefault(b.task_id, []).append(b)

    items: list[PlanDiffItem] = []
    added = 0
    moved = 0
    deleted = 0

    # Find deleted and moved blocks
    for task_id, old_list in old_by_task.items():
        new_list = new_by_task.get(task_id, [])
        for i, ob in enumerate(old_list):
            if i < len(new_list):
                nb = new_list[i]
                if ob.start != nb.start or ob.end != nb.end:
                    items.append(PlanDiffItem(
                        action="moved",
                        block_id=ob.id,
                        task_title=titles.get(task_id, ""),
                        old_start=ob.start,
                        old_end=ob.end,
                        new_start=nb.start,
                        new_end=nb.end,
                    ))
                    moved += 1
            else:
                items.append(PlanDiffItem(
                    action="deleted",
                    block_id=ob.id,
                    task_title=titles.get(task_id, ""),
                    old_start=ob.start,
                    old_end=ob.end,
                ))
                deleted += 1

    # Find added blocks
    for task_id, new_list in new_by_task.items():
        old_count = len(old_by_task.get(task_id, []))
        for nb in new_list[old_count:]:
            items.append(PlanDiffItem(
                action="added",
                task_title=titles.get(task_id, ""),
                new_start=nb.start,
                new_end=nb.end,
            ))
            added += 1

    return PlanDiffResponse(added=added, moved=moved, deleted=deleted, items=items)
