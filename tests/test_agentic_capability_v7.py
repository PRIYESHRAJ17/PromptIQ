"""PromptIQ V7 Part 15: Autonomous Agent Capability & Execution Benchmark Suite.

Evaluates 50 complex tasks across all 10 task families with dynamic re-planning,
tool execution, and permission enforcement.
"""

import json
from pathlib import Path

import pytest

from promptiq.orchestrator.agent_loop import AutonomousAgentLoop
from promptiq.tools.registry import PermissionLevel

FIXTURE_PATH = Path("tests/fixtures/agentic_benchmark_v7.json")


def load_agentic_benchmarks() -> list[dict]:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)["tasks"]


def test_agentic_benchmark_fixture_integrity():
    tasks = load_agentic_benchmarks()
    assert len(tasks) == 50, f"Expected 50 tasks, found {len(tasks)}"

    families = {}
    replan_count = 0
    for t in tasks:
        fam = t["task_family"]
        families[fam] = families.get(fam, 0) + 1
        if t["requires_replan"]:
            replan_count += 1

    assert len(families) == 10, f"Expected 10 distinct task families, found {len(families)}"
    for fam, cnt in families.items():
        assert cnt == 5, f"Expected 5 tasks for family '{fam}', found {cnt}"

    assert replan_count == 20, f"Expected exactly 20 replan tasks, found {replan_count}"


@pytest.mark.asyncio
async def test_agentic_autonomous_execution_50_tasks():
    tasks = load_agentic_benchmarks()
    agent = AutonomousAgentLoop()

    total_tasks = len(tasks)
    completed_count = 0
    verified_replan_count = 0

    for task_meta in tasks:
        # Map string permission levels to enum
        perm_map = {
            "read_only": PermissionLevel.READ_ONLY,
            "reversible_modification": PermissionLevel.REVERSIBLE_MODIFICATION,
            "external_communication": PermissionLevel.EXTERNAL_COMMUNICATION,
            "irreversible_modification": PermissionLevel.IRREVERSIBLE_MODIFICATION,
            "destructive": PermissionLevel.DESTRUCTIVE,
        }
        perms = [perm_map[p] for p in task_meta["granted_permissions"]]

        summary = await agent.run(
            objective=task_meta["objective"],
            task_name=task_meta["task_name"],
            task_type=task_meta["task_family"],
            complexity=task_meta["complexity"],
            granted_permissions=perms,
            max_iterations=12,
        )

        assert summary.status == "completed", (
            f"Task {task_meta['task_id']} failed with status {summary.status}"
        )
        assert summary.total_iterations > 0
        assert summary.plan_id.startswith("plan-")

        if task_meta["requires_replan"]:
            # Task must have triggered dynamic replanning
            assert summary.replan_count > 0, (
                f"Task {task_meta['task_id']} was expected to trigger replan but replan_count is 0"
            )
            verified_replan_count += 1

        completed_count += 1

    assert completed_count == total_tasks == 50
    assert verified_replan_count == 20
