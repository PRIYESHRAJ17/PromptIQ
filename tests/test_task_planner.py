"""Tests for PromptIQ Hierarchical Task Planning Engine and DAG Decomposer."""

from promptiq.orchestrator.planner import (
    ExecutionLoopStage,
    ExecutionPlan,
    SubtaskStatus,
    TaskPlanningEngine,
)


def test_task_planner_decomposition_basic():
    plan = TaskPlanningEngine.decompose_task(
        task_name="Standard Prompt Synthesis",
        task_type="prompt_synthesis",
        goal="Generate a prompt for SQL generation",
        complexity="low",
    )
    assert isinstance(plan, ExecutionPlan)
    assert plan.status == "initialized"
    assert len(plan.subtasks) >= 6
    assert plan.critical_path

    # First task should be intent analysis
    executable = TaskPlanningEngine.get_executable_subtasks(plan)
    assert len(executable) == 1
    assert executable[0].id == "task-01-intent"


def test_task_planner_decomposition_complex_research():
    plan = TaskPlanningEngine.decompose_task(
        task_name="Agent Architecture Design",
        task_type="ai_agent_development",
        goal="Design an autonomous research agent",
        complexity="high",
    )
    assert any(t.id == "task-02-research" for t in plan.subtasks)
    subtask_ids = [t.id for t in plan.subtasks]
    assert "task-02-research" in subtask_ids

    # Simulate execution progress
    executable = TaskPlanningEngine.get_executable_subtasks(plan)
    assert len(executable) == 1
    assert executable[0].id == "task-01-intent"

    # Mark intent completed
    executable[0].status = SubtaskStatus.COMPLETED

    # Now research should be executable
    executable2 = TaskPlanningEngine.get_executable_subtasks(plan)
    assert len(executable2) == 1
    assert executable2[0].id == "task-02-research"


def test_execution_loop_stages_enum():
    stages = [s.value for s in ExecutionLoopStage]
    assert "understand" in stages
    assert "discover" in stages
    assert "specify" in stages
    assert "plan" in stages
    assert "execute" in stages
    assert "inspect" in stages
    assert "critique" in stages
    assert "revise" in stages
    assert "verify" in stages
    assert "deliver" in stages
    assert "remember" in stages
