from pydantic import BaseModel


class AvailabilityGridSchema(BaseModel):
    """7 days × 96 slots (15-min each). True = available."""

    monday: list[bool] = [False] * 96
    tuesday: list[bool] = [False] * 96
    wednesday: list[bool] = [False] * 96
    thursday: list[bool] = [False] * 96
    friday: list[bool] = [False] * 96
    saturday: list[bool] = [False] * 96
    sunday: list[bool] = [False] * 96


class SchedulingRulesSchema(BaseModel):
    daily_max_hours: float = 8.0
    break_after_minutes: int = 90
    break_duration_minutes: int = 15
    max_consecutive_same_subject_minutes: int = 120
    preferred_start_hour: int = 8
    preferred_end_hour: int = 22
    slot_duration_minutes: int = 15
    sleep_start_hour: int = 23
    sleep_end_hour: int = 7
    lighter_weekends: bool = True
    weekend_max_hours: float = 4.0
