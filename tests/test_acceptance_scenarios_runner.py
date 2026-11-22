"""Tests for Acceptance Scenarios Runner executing all 10 task family scenarios."""

import pytest

from promptiq.acceptance.runner import (
    run_all_acceptance_scenarios,
    run_scenario_5_prompt_improvement,
    setup_test_workspace_and_user,
)
from promptiq.core.database import async_session_factory, init_db
from promptiq.schemas.acceptance import ExecutionState


@pytest.mark.asyncio
async def test_acceptance_runner_e2e_all_scenarios():
    """Executes the master acceptance scenarios runner through all 10 task families."""
    await init_db()

    async with async_session_factory() as db:
        user, ws = await setup_test_workspace_and_user(db)
        summary = await run_all_acceptance_scenarios(db, user, ws)
        await db.commit()

    assert summary.total_scenarios == 10
    assert summary.overall_verdict in ("PASS", "CONDITIONAL_PASS")
    assert summary.fully_verified_count >= 4
    assert summary.completed_with_warnings_count >= 4
    assert summary.blocked_count == 0
    assert summary.failed_count == 0


@pytest.mark.asyncio
async def test_scenario_5_unresolved_finding_transitions_to_warnings():
    """Proves that when resolve_testability=False, Scenario 5 is classified COMPLETED_WITH_WARNINGS."""
    await init_db()

    async with async_session_factory() as db:
        user, ws = await setup_test_workspace_and_user(db)
        trace = await run_scenario_5_prompt_improvement(db, user, ws, resolve_testability=False)
        await db.commit()

    assert trace.terminal_state == ExecutionState.COMPLETED_WITH_WARNINGS
    assert len(trace.unresolved_findings) >= 1
    assert any(f["category"] == "testability_gap" for f in trace.unresolved_findings)
