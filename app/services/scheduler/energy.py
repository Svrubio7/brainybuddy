"""
Energy profile scoring for the scheduling engine.

Each user has an energy profile that maps hours of the day to a 0-1 score
indicating their cognitive capacity. The scheduler uses this to place
demanding tasks at high-energy times and lighter tasks at low-energy times.
"""

import enum
import math

from pydantic import BaseModel, Field


class EnergyProfileType(str, enum.Enum):
    MORNING_PERSON = "morning_person"
    NIGHT_OWL = "night_owl"
    BALANCED = "balanced"


class EnergyProfile(BaseModel):
    """
    Energy profile with hourly scores (0-1) for each hour of the day.

    hourly_scores[0] = midnight, hourly_scores[12] = noon, etc.
    """

    profile_type: EnergyProfileType = EnergyProfileType.BALANCED
    hourly_scores: list[float] = Field(
        default_factory=lambda: [0.5] * 24,
        min_length=24,
        max_length=24,
        description="Energy score 0.0-1.0 for each hour (index 0 = midnight)",
    )


def _bell_curve(peak_hour: float, spread: float, hour: int) -> float:
    """Generate a bell-curve score centred on peak_hour with given spread."""
    distance = min(abs(hour - peak_hour), 24 - abs(hour - peak_hour))
    return max(0.05, math.exp(-0.5 * (distance / spread) ** 2))


def get_default_profiles() -> dict[EnergyProfileType, EnergyProfile]:
    """Return three preset energy profiles."""

    # Morning person: peaks around 9-10 AM, drops sharply after 6 PM
    morning_scores: list[float] = []
    for h in range(24):
        score = _bell_curve(peak_hour=9.5, spread=4.0, hour=h)
        # Extra penalty for late night
        if h >= 21 or h < 5:
            score *= 0.3
        morning_scores.append(round(min(1.0, score), 2))

    # Night owl: peaks around 9-10 PM, low in early morning
    night_scores: list[float] = []
    for h in range(24):
        score = _bell_curve(peak_hour=21.0, spread=4.5, hour=h)
        # Extra penalty for early morning
        if 5 <= h <= 9:
            score *= 0.4
        night_scores.append(round(min(1.0, score), 2))

    # Balanced: two moderate peaks (late morning + early afternoon)
    balanced_scores: list[float] = []
    for h in range(24):
        morning_peak = _bell_curve(peak_hour=10.0, spread=3.5, hour=h)
        afternoon_peak = _bell_curve(peak_hour=15.0, spread=3.0, hour=h)
        score = max(morning_peak, afternoon_peak)
        # Penalty for sleep hours
        if h >= 23 or h < 6:
            score *= 0.2
        balanced_scores.append(round(min(1.0, score), 2))

    return {
        EnergyProfileType.MORNING_PERSON: EnergyProfile(
            profile_type=EnergyProfileType.MORNING_PERSON,
            hourly_scores=morning_scores,
        ),
        EnergyProfileType.NIGHT_OWL: EnergyProfile(
            profile_type=EnergyProfileType.NIGHT_OWL,
            hourly_scores=night_scores,
        ),
        EnergyProfileType.BALANCED: EnergyProfile(
            profile_type=EnergyProfileType.BALANCED,
            hourly_scores=balanced_scores,
        ),
    }


# Focus-load weights: how much the energy score matters for each load level.
# Deep-focus tasks are penalised heavily at low-energy hours; light tasks
# are almost unaffected by energy.
_FOCUS_LOAD_WEIGHT = {
    "deep": 0.9,
    "medium": 0.5,
    "light": 0.2,
}


def score_slot_for_task(
    hour: int,
    focus_load: str,
    profile: EnergyProfile,
) -> float:
    """
    Score a time slot (0.0-1.0) for scheduling a task.

    Higher scores mean the slot is a better fit.

    Parameters
    ----------
    hour : int
        Hour of the day (0-23).
    focus_load : str
        One of "light", "medium", "deep" (see app.models.task.FocusLoad).
    profile : EnergyProfile
        The user's energy profile.

    Returns
    -------
    float
        Score between 0.0 and 1.0.
    """
    if hour < 0 or hour > 23:
        return 0.0

    energy = profile.hourly_scores[hour]
    weight = _FOCUS_LOAD_WEIGHT.get(focus_load, 0.5)

    # Blend: base score (0.5) adjusted towards energy by weight
    # For deep tasks, energy matters a lot; for light tasks, barely.
    score = (1.0 - weight) * 0.5 + weight * energy
    return round(max(0.0, min(1.0, score)), 3)
