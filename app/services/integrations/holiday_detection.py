"""Holiday detection and reduced-availability detection service.

Uses the `holidays` library to identify public holidays and
provides heuristics for detecting travel/vacation periods that
should reduce a student's available study time.
"""

import logging
from datetime import date, timedelta
from typing import Any

import holidays

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_holidays(
    country: str,
    year: int,
    state: str | None = None,
) -> list[dict[str, Any]]:
    """Return public holidays for a country and year.

    Args:
        country: ISO 3166-1 alpha-2 country code (e.g. 'US', 'ES', 'DE').
        year: Calendar year.
        state: Optional state/province code for sub-national holidays.

    Returns:
        Sorted list of dicts with 'date' (ISO string) and 'name'.
    """
    try:
        kwargs: dict[str, Any] = {"years": year}
        if state:
            kwargs["state"] = state

        country_holidays = holidays.country_holidays(country, **kwargs)

        result = [
            {"date": d.isoformat(), "name": name}
            for d, name in sorted(country_holidays.items())
        ]
        return result
    except Exception as exc:
        logger.error("Failed to fetch holidays for %s/%d: %s", country, year, exc)
        return []


def is_holiday(country: str, check_date: date, state: str | None = None) -> bool:
    """Check if a specific date is a public holiday."""
    try:
        kwargs: dict[str, Any] = {}
        if state:
            kwargs["state"] = state
        country_holidays = holidays.country_holidays(country, **kwargs)
        return check_date in country_holidays
    except Exception:
        return False


async def detect_reduced_availability(
    user_id: int,
    date_range: tuple[date, date],
    country: str = "US",
    state: str | None = None,
) -> list[dict[str, Any]]:
    """Detect dates with reduced availability within a date range.

    Combines:
    1. Public holidays (from the holidays library)
    2. Holiday-adjacent days (day before/after a holiday -- potential travel)
    3. Multi-day holiday clusters (e.g. Thanksgiving week)
    4. Academic break detection (based on common patterns)

    Args:
        user_id: The user whose availability to check.
        date_range: Tuple of (start_date, end_date) inclusive.
        country: ISO country code.
        state: Optional state/province.

    Returns:
        List of dicts with 'date', 'reason', 'availability_factor' (0.0-1.0).
    """
    start_date, end_date = date_range
    results: list[dict[str, Any]] = []
    seen_dates: set[date] = set()

    # Collect years in range
    years = set()
    d = start_date
    while d <= end_date:
        years.add(d.year)
        d += timedelta(days=365)
    years.add(end_date.year)

    # Get all holidays across relevant years
    all_holidays: dict[date, str] = {}
    for year in years:
        try:
            kwargs: dict[str, Any] = {"years": year}
            if state:
                kwargs["state"] = state
            country_holidays = holidays.country_holidays(country, **kwargs)
            for h_date, h_name in country_holidays.items():
                if start_date <= h_date <= end_date:
                    all_holidays[h_date] = h_name
        except Exception as exc:
            logger.warning("Holiday lookup failed for year %d: %s", year, exc)

    # 1. Mark holidays as reduced availability
    for h_date, h_name in all_holidays.items():
        results.append({
            "date": h_date.isoformat(),
            "reason": f"Public holiday: {h_name}",
            "availability_factor": 0.2,
            "type": "holiday",
        })
        seen_dates.add(h_date)

    # 2. Travel days (day before/after each holiday)
    for h_date in list(all_holidays.keys()):
        for offset in (-1, 1):
            travel_date = h_date + timedelta(days=offset)
            if (
                start_date <= travel_date <= end_date
                and travel_date not in seen_dates
            ):
                results.append({
                    "date": travel_date.isoformat(),
                    "reason": f"Potential travel day (near {all_holidays[h_date]})",
                    "availability_factor": 0.5,
                    "type": "travel",
                })
                seen_dates.add(travel_date)

    # 3. Detect holiday clusters (3+ holidays within 7 days → mark the gap)
    holiday_dates = sorted(all_holidays.keys())
    for i in range(len(holiday_dates) - 1):
        gap = (holiday_dates[i + 1] - holiday_dates[i]).days
        if 2 <= gap <= 5:
            # Fill gap days between close holidays
            for offset in range(1, gap):
                gap_date = holiday_dates[i] + timedelta(days=offset)
                if (
                    start_date <= gap_date <= end_date
                    and gap_date not in seen_dates
                ):
                    results.append({
                        "date": gap_date.isoformat(),
                        "reason": "Holiday cluster gap (likely break)",
                        "availability_factor": 0.3,
                        "type": "cluster_gap",
                    })
                    seen_dates.add(gap_date)

    # 4. Common academic break patterns (rough heuristics)
    for year in years:
        academic_breaks = _get_academic_break_ranges(year)
        for break_start, break_end, break_name in academic_breaks:
            d = max(break_start, start_date)
            while d <= min(break_end, end_date):
                if d not in seen_dates:
                    results.append({
                        "date": d.isoformat(),
                        "reason": f"Academic break: {break_name}",
                        "availability_factor": 0.4,
                        "type": "academic_break",
                    })
                    seen_dates.add(d)
                d += timedelta(days=1)

    # Sort by date
    results.sort(key=lambda r: r["date"])
    return results


def _get_academic_break_ranges(year: int) -> list[tuple[date, date, str]]:
    """Return approximate academic break date ranges for a given year.

    These are rough defaults; users can override with their own calendar.
    """
    return [
        # Winter break (end of December to early January)
        (date(year, 12, 20), date(year, 12, 31), "Winter break"),
        (date(year, 1, 1), date(year, 1, 7), "Winter break"),
        # Spring break (mid-March, very approximate)
        (date(year, 3, 10), date(year, 3, 18), "Spring break"),
    ]
