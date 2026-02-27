"""
SM-2 spaced repetition algorithm for scheduling review sessions.

Based on the SuperMemo SM-2 algorithm by Piotr Wozniak.

Quality grades:
  0 - Complete blackout, no recall at all
  1 - Incorrect response but upon seeing the answer, remembered
  2 - Incorrect response but the answer seemed easy to recall
  3 - Correct response with significant difficulty
  4 - Correct response after some hesitation
  5 - Perfect response with no hesitation
"""

from datetime import date, timedelta

from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    """Output of a single SM-2 computation step."""

    next_interval: int = Field(description="Days until next review")
    repetitions: int = Field(description="Updated repetition count")
    easiness: float = Field(description="Updated easiness factor (>= 1.3)")


class ReviewBlock(BaseModel):
    """A scheduled review date for a specific task."""

    task_id: int
    review_date: date
    repetition_number: int
    expected_interval: int = Field(description="Interval in days that led to this date")


def compute_next_review(
    quality: int,
    repetitions: int = 0,
    easiness: float = 2.5,
    interval: int = 1,
) -> ReviewResult:
    """
    Compute the next review interval using the SM-2 algorithm.

    Parameters
    ----------
    quality : int
        Quality of the recall, 0-5 (see module docstring).
    repetitions : int
        Number of consecutive correct recalls so far.
    easiness : float
        Current easiness factor (EF), starts at 2.5.
    interval : int
        Current interval in days.

    Returns
    -------
    ReviewResult
        Updated interval, repetition count, and easiness factor.
    """
    quality = max(0, min(5, quality))

    # Update easiness factor
    new_easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_easiness = max(1.3, new_easiness)

    if quality < 3:
        # Failed recall — reset to the beginning
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = max(1, round(interval * new_easiness))

    return ReviewResult(
        next_interval=new_interval,
        repetitions=new_repetitions,
        easiness=round(new_easiness, 2),
    )


def generate_review_blocks(
    task_id: int,
    exam_date: date,
    start_date: date | None = None,
    initial_easiness: float = 2.5,
    assumed_quality: int = 4,
    max_reviews: int = 20,
) -> list[ReviewBlock]:
    """
    Generate a list of review dates from start_date up to exam_date.

    The function projects forward using the SM-2 algorithm, assuming
    a fixed quality grade for each review (default: 4, "correct after
    some hesitation"). This gives the student a schedule to follow;
    actual quality tracking happens at review time.

    Parameters
    ----------
    task_id : int
        The task (material) to review.
    exam_date : date
        The date of the exam / deadline. Reviews stop before this date.
    start_date : date | None
        When to begin reviews. Defaults to today.
    initial_easiness : float
        Starting easiness factor.
    assumed_quality : int
        The quality grade assumed for projecting the schedule (0-5).
    max_reviews : int
        Safety cap on the number of review blocks.

    Returns
    -------
    list[ReviewBlock]
        Chronologically ordered review dates.
    """
    if start_date is None:
        start_date = date.today()

    if start_date >= exam_date:
        return []

    blocks: list[ReviewBlock] = []
    current_date = start_date
    repetitions = 0
    easiness = initial_easiness
    interval = 1
    review_number = 0

    while current_date < exam_date and review_number < max_reviews:
        blocks.append(
            ReviewBlock(
                task_id=task_id,
                review_date=current_date,
                repetition_number=review_number,
                expected_interval=interval,
            )
        )
        review_number += 1

        result = compute_next_review(
            quality=assumed_quality,
            repetitions=repetitions,
            easiness=easiness,
            interval=interval,
        )
        repetitions = result.repetitions
        easiness = result.easiness
        interval = result.next_interval

        current_date = current_date + timedelta(days=interval)

    # If the last review lands on or after the exam, ensure there is at
    # least a cram session the day before the exam.
    day_before_exam = exam_date - timedelta(days=1)
    if blocks and blocks[-1].review_date < day_before_exam:
        blocks.append(
            ReviewBlock(
                task_id=task_id,
                review_date=day_before_exam,
                repetition_number=review_number,
                expected_interval=1,
            )
        )

    return blocks
