"""Tests for PromptIQ Task Family Specialization across 200 scenarios."""

import json
from pathlib import Path

from promptiq.orchestrator.planner import TaskPlanningEngine
from promptiq.registry.task_families import TaskFamilyRegistry

FIXTURE_PATH = Path("tests/fixtures/task_families_benchmark_v7.json")


def load_task_family_scenarios() -> list[dict]:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)["scenarios"]


def test_task_families_fixture_structure():
    scenarios = load_task_family_scenarios()
    assert len(scenarios) == 200
    dev_count = sum(1 for s in scenarios if not s["is_held_out"])
    held_out_count = sum(1 for s in scenarios if s["is_held_out"])
    assert dev_count == 100
    assert held_out_count == 100

    families = {s["task_family"] for s in scenarios}
    assert len(families) == 10


def test_task_family_dag_specialization_dev():
    scenarios = [s for s in load_task_family_scenarios() if not s["is_held_out"]]
    assert len(scenarios) == 100

    for sc in scenarios:
        family_id = sc["task_family"]
        family_meta = TaskFamilyRegistry.get_family(family_id)
        assert family_meta is not None
        assert family_meta.id == family_id

        plan = TaskPlanningEngine.decompose_task(
            task_name=sc["scenario_id"],
            task_type=family_id,
            goal=sc["goal"],
            constraints=sc["constraints"],
        )

        subtask_ids = [t.id for t in plan.subtasks]
        # Check expected DAG subtasks exist in plan
        for exp_st in sc["expected_dag_subtasks"]:
            assert exp_st in subtask_ids, (
                f"Task family {family_id} missing expected subtask {exp_st}"
            )


def test_task_family_dag_specialization_held_out():
    scenarios = [s for s in load_task_family_scenarios() if s["is_held_out"]]
    assert len(scenarios) == 100

    for sc in scenarios:
        family_id = sc["task_family"]
        family_meta = TaskFamilyRegistry.get_family(family_id)
        assert family_meta is not None

        plan = TaskPlanningEngine.decompose_task(
            task_name=sc["scenario_id"],
            task_type=family_id,
            goal=sc["goal"],
            constraints=sc["constraints"],
        )

        assert len(plan.subtasks) >= 4
        assert plan.critical_path
        assert plan.task_type == family_id
