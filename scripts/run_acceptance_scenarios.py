"""Comprehensive runner executing all 5 PromptIQ product intelligence scenarios with strict Quality Gates.

Validates:
1. Software Engineering (software_project)
2. Academic & Technical Research (research)
3. AI Agent Development (agent_creation)
4. Business Strategy (business_strategy)
5. General Prompt Improvement (prompt_improvement)

Enforces cryptographic artifact binding, state machine transition validation,
revision verification, and honest evidence-backed terminal states.
"""

import asyncio
import json
from pathlib import Path

from promptiq.acceptance.runner import (
    run_all_acceptance_scenarios,
    setup_test_workspace_and_user,
)
from promptiq.core.database import async_session_factory, init_db

TRACE_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE.json")
TRACE_V2_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE_V2.json")


async def main():
    print("=" * 80)
    print("PROMPTIQ MASTER ACCEPTANCE RUNNER — QUALITY GATES & STATE MACHINE ENFORCEMENT")
    print("=" * 80)
    await init_db()

    async with async_session_factory() as db:
        user, ws = await setup_test_workspace_and_user(db)
        print(f"Provisioned operator: {user.email} (Workspace: {ws.id})")

        print("\nExecuting all 5 acceptance scenarios under strict quality gates...")
        summary = await run_all_acceptance_scenarios(db, user, ws)
        await db.commit()

    print("\n" + "=" * 80)
    print(f"EXECUTION COMPLETED — OVERALL VERDICT: {summary.overall_verdict}")
    print(f"Total Scenarios: {summary.total_scenarios}")
    print(f"Fully Verified: {summary.fully_verified_count}")
    print(f"Completed with Warnings: {summary.completed_with_warnings_count}")
    print(f"Blocked: {summary.blocked_count}")
    print(f"Failed: {summary.failed_count}")
    print("=" * 80)

    for s in summary.scenarios:
        term = s.terminal_state.value if s.terminal_state else "UNKNOWN"
        print(
            f" - [{s.scenario_id}] State: {term} (Warnings: {len(s.warnings)}, Open findings: {len(s.unresolved_findings)})"
        )

    summary_dict = summary.model_dump(mode="json")

    TRACE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)

    with open(TRACE_V2_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)

    print(
        f"\nAudit traces successfully persisted to:\n - {TRACE_OUTPUT_PATH}\n - {TRACE_V2_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    asyncio.run(main())
