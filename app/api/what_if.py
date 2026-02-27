"""What-if simulation API routes."""

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.services.scheduler.what_if import Scenario, SimulationResult, simulate_scenario

router = APIRouter(prefix="/api/what-if", tags=["what-if"])


@router.post("/simulate", response_model=SimulationResult)
async def run_simulation(
    scenario: Scenario,
    user: CurrentUser,
    session: DbSession,
):
    """
    Run a what-if simulation against the user's current plan.

    Accepts a hypothetical scenario and returns the diff that *would*
    occur if the scenario were applied.  Nothing is persisted.
    """
    return await simulate_scenario(session, user.id, scenario)
