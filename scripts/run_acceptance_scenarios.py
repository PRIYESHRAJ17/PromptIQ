"""Comprehensive runner executing all 10 PromptIQ product intelligence scenarios with strict Quality Gates.

Validates:
1. Software Engineering (software_project)
2. Academic & Technical Research (research)
3. AI Agent Development (agent_creation)
4. Business Strategy (business_strategy)
5. General Prompt Improvement (prompt_improvement)
6. Product Development & PRD (product_development)
7. Writing & Long-Form Content (writing_content)
8. Data Analytics & Pipeline Engineering (data_analysis)
9. Technical Documentation (technical_documentation)
10. Education & Curriculum Design (education_learning)

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
from promptiq.acceptance.validator import AcceptanceTraceValidator
from promptiq.core.database import async_session_factory, init_db

TRACE_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE.json")
TRACE_V2_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE_V2.json")
TRACE_V3_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE_V3.json")
TRACE_V4_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE_V4.json")
TRACE_V5_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE_V5.json")
TRACE_V6_OUTPUT_PATH = Path("docs/ACCEPTANCE_SCENARIOS_TRACE_V6.json")


async def main():
    print("=" * 80)
    print("PROMPTIQ MASTER ACCEPTANCE RUNNER — 10 TASK FAMILIES & QUALITY GATES")
    print("=" * 80)
    await init_db()

    async with async_session_factory() as db:
        user, ws = await setup_test_workspace_and_user(db)
        print(f"Provisioned operator: {user.email} (Workspace: {ws.id})")

        print("\nExecuting all 10 acceptance scenarios under strict quality gates...")
        summary = await run_all_acceptance_scenarios(db, user, ws)
        await db.commit()

        summary_dict = summary.model_dump(mode="json")

        TRACE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        for p in (TRACE_OUTPUT_PATH, TRACE_V2_OUTPUT_PATH, TRACE_V3_OUTPUT_PATH, TRACE_V4_OUTPUT_PATH, TRACE_V5_OUTPUT_PATH, TRACE_V6_OUTPUT_PATH):
            with open(p, "w", encoding="utf-8") as f:
                json.dump(summary_dict, f, indent=2)

        print("\n" + "=" * 80)
        print("RUNNING INDEPENDENT ACCEPTANCE TRACE & AUTHORITATIVE PERSISTENCE VALIDATION")
        print("=" * 80)
        validator = AcceptanceTraceValidator(summary_dict)
        val_report = validator.validate_all()
        print(f"Independent Structural & Invariant Suites: {'PASS' if val_report.is_valid else 'FAIL'} ({val_report.passed_checks}/{val_report.total_checks_evaluated} checks passed)")
        if val_report.errors:
            for err in val_report.errors:
                print(f"  [FAIL] {err.check_name}: {err.message}")

        auth_report = await validator.validate_authoritative_persistence(db=db)
        print(f"Authoritative 5-Layer Persistence Validation: {'PASS' if auth_report.is_valid else 'FAIL'}")
        for _l_key, l_res in auth_report.layers.items():
            print(f"  - [{l_res.layer}] {l_res.name}: {l_res.status} (Errors: {len(l_res.errors)})")
            for e in l_res.errors:
                print(f"      * {e}")

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

    print(
        f"\nAudit traces successfully persisted to:\n - {TRACE_OUTPUT_PATH}\n - {TRACE_V2_OUTPUT_PATH}\n - {TRACE_V3_OUTPUT_PATH}\n - {TRACE_V4_OUTPUT_PATH}\n - {TRACE_V5_OUTPUT_PATH}\n - {TRACE_V6_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    asyncio.run(main())
