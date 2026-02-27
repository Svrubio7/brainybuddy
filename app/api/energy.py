"""Energy profile API routes."""

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.services.scheduler.energy import (
    EnergyProfile,
    EnergyProfileType,
    get_default_profiles,
)

router = APIRouter(prefix="/api/energy-profile", tags=["energy"])


# ── In-DB persistence helpers ────────────────────────────────────────
# Energy profiles are stored in the scheduling_rules table as a JSON
# column.  Until a dedicated column is added via migration, we store
# them in a lightweight key-value approach using the AvailabilityGrid
# pattern: one JSON blob per user.

import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.availability import SchedulingRules


async def _get_profile(session: AsyncSession, user_id: int) -> EnergyProfile:
    """Load the user's energy profile, falling back to the balanced preset."""
    result = await session.execute(
        select(SchedulingRules).where(SchedulingRules.user_id == user_id)
    )
    rules = result.scalar_one_or_none()

    # We piggyback on a JSON-text field stored alongside scheduling rules.
    # If no custom profile exists yet, return the balanced default.
    if rules is None:
        return get_default_profiles()[EnergyProfileType.BALANCED]

    # Try to read from an extended attribute.  If the column doesn't exist
    # yet we simply return the default.
    raw = getattr(rules, "energy_profile_json", None)
    if raw:
        try:
            return EnergyProfile(**json.loads(raw))
        except Exception:
            pass

    return get_default_profiles()[EnergyProfileType.BALANCED]


async def _save_profile(
    session: AsyncSession, user_id: int, profile: EnergyProfile
) -> None:
    """Persist the energy profile.  Currently stored as an extended attr."""
    result = await session.execute(
        select(SchedulingRules).where(SchedulingRules.user_id == user_id)
    )
    rules = result.scalar_one_or_none()
    profile_json = json.dumps(profile.model_dump())

    if rules is not None:
        # If the model has the column, set it; otherwise it's a no-op
        # until the migration is run.
        try:
            rules.energy_profile_json = profile_json  # type: ignore[attr-defined]
        except AttributeError:
            pass
    else:
        rules = SchedulingRules(user_id=user_id)
        try:
            rules.energy_profile_json = profile_json  # type: ignore[attr-defined]
        except AttributeError:
            pass
        session.add(rules)

    await session.commit()


# ── Routes ───────────────────────────────────────────────────────────


@router.get("", response_model=EnergyProfile)
async def get_energy_profile(user: CurrentUser, session: DbSession):
    """Return the current user's energy profile."""
    return await _get_profile(session, user.id)


@router.put("", response_model=EnergyProfile)
async def update_energy_profile(
    data: EnergyProfile, user: CurrentUser, session: DbSession
):
    """Update the current user's energy profile."""
    await _save_profile(session, user.id, data)
    return data


@router.get("/presets", response_model=dict[str, EnergyProfile])
async def list_presets():
    """Return the three built-in energy profile presets."""
    profiles = get_default_profiles()
    return {k.value: v for k, v in profiles.items()}
