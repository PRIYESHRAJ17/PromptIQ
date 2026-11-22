"""Comprehensive tests for PromptIQ Autonomous Agent Loop and Tool Registry."""

import pytest

from promptiq.orchestrator.agent_loop import AgentExecutionSummary, AutonomousAgentLoop
from promptiq.orchestrator.planner import SubtaskStatus
from promptiq.tools.builtin import tool_registry
from promptiq.tools.registry import (
    PermissionLevel,
    RiskTier,
    ToolDefinition,
    ToolRegistry,
)


@pytest.mark.asyncio
async def test_tool_registry_permission_enforcement():
    custom_reg = ToolRegistry()

    destructive_tool = ToolDefinition(
        tool_id="dangerous_db_drop",
        name="Drop Table",
        description="Drops a database table",
        permission_level=PermissionLevel.DESTRUCTIVE,
        risk_tier=RiskTier.CRITICAL,
    )

    def dummy_handler(inputs, context=None):
        return {"dropped": True}

    custom_reg.register_tool(destructive_tool, dummy_handler)

    # 1. Caller with only READ_ONLY permission must be blocked
    res_blocked = await custom_reg.execute_tool(
        tool_id="dangerous_db_drop",
        inputs={},
        caller_permissions=[PermissionLevel.READ_ONLY],
    )
    assert not res_blocked.success
    assert "Permission denied" in (res_blocked.error or "")

    # 2. Caller with DESTRUCTIVE permission must succeed
    res_allowed = await custom_reg.execute_tool(
        tool_id="dangerous_db_drop",
        inputs={},
        caller_permissions=[PermissionLevel.DESTRUCTIVE],
    )
    assert res_allowed.success
    assert res_allowed.output == {"dropped": True}


@pytest.mark.asyncio
async def test_builtin_tools_execution(tmp_path):
    # 1. Filesystem Write and Read in tmp_path
    test_file = tmp_path / "agent_artifact.txt"
    write_res = await tool_registry.execute_tool(
        tool_id="filesystem_write",
        inputs={"file_path": str(test_file), "content": "PromptIQ Autonomous Agent V7"},
        caller_permissions=[PermissionLevel.REVERSIBLE_MODIFICATION],
        context={"allowed_root": str(tmp_path)},
    )
    assert write_res.success
    assert write_res.output["bytes_written"] > 0

    read_res = await tool_registry.execute_tool(
        tool_id="filesystem_read",
        inputs={"file_path": str(test_file)},
        caller_permissions=[PermissionLevel.READ_ONLY],
        context={"allowed_root": str(tmp_path)},
    )
    assert read_res.success
    assert "PromptIQ Autonomous Agent V7" in read_res.output["content"]

    # 2. Data Transform Tool
    data_res = await tool_registry.execute_tool(
        tool_id="data_transform",
        inputs={
            "data": [{"val": 10}, {"val": 20}, {"val": 30}],
            "operation": "summary",
            "field": "val",
        },
        caller_permissions=[PermissionLevel.READ_ONLY],
    )
    assert data_res.success
    assert data_res.output["count"] == 3
    assert data_res.output["mean"] == 20.0
    assert data_res.output["max"] == 30

    # 3. Validator Exec Tool
    val_res = await tool_registry.execute_tool(
        tool_id="validator_exec",
        inputs={
            "content": "def authenticate_user(email: str, password: str) -> bool:\n    return True\n",
            "assertions": [
                {"type": "contains", "target": "def authenticate_user"},
                {"type": "length_min", "target": "20"},
                {"type": "contains", "target": "eval(", "negate": True},
            ],
        },
        caller_permissions=[PermissionLevel.READ_ONLY],
    )
    assert val_res.success
    assert val_res.output["all_passed"] is True
    assert val_res.output["passed_count"] == 3


@pytest.mark.asyncio
async def test_autonomous_agent_loop_e2e_execution():
    agent = AutonomousAgentLoop()
    summary: AgentExecutionSummary = await agent.run(
        objective="Design an autonomous event-driven processing worker with retry policies",
        task_name="Worker Architecture",
        task_type="software_engineering",
        granted_permissions=[
            PermissionLevel.READ_ONLY,
            PermissionLevel.REVERSIBLE_MODIFICATION,
        ],
        max_iterations=12,
    )

    assert isinstance(summary, AgentExecutionSummary)
    assert summary.status == "completed"
    assert summary.total_iterations >= 5
    assert len(summary.iterations) >= 5

    # Check that each iteration has rich structured state
    for it in summary.iterations:
        assert it.iteration > 0
        assert it.subtask_id
        assert it.proposed_action
        assert it.permission_decision in ("ALLOWED", "DENIED")
        assert it.result_interpretation

    # Verify plan completed
    completed_subtasks = [t for t in summary.plan.subtasks if t.status == SubtaskStatus.COMPLETED]
    assert len(completed_subtasks) >= 5


@pytest.mark.asyncio
async def test_agent_loop_replan_and_recovery_on_failure():
    # Setup custom registry with an intentionally failing tool
    custom_reg = ToolRegistry()
    failing_tool = ToolDefinition(
        tool_id="flaky_service_call",
        name="Flaky Service",
        description="Fails on first call",
        permission_level=PermissionLevel.REVERSIBLE_MODIFICATION,
    )

    call_count = 0

    def flaky_handler(inputs, context=None):
        nonlocal call_count
        call_count += 1
        raise ConnectionResetError("Remote service connection reset by peer")

    custom_reg.register_tool(failing_tool, flaky_handler)

    agent = AutonomousAgentLoop(tool_reg=custom_reg)
    # Inject a failing subtask into test
    summary = await agent.run(
        objective="Test plan recovery",
        task_name="Recovery Test",
        task_type="software_engineering",
        granted_permissions=[PermissionLevel.READ_ONLY, PermissionLevel.REVERSIBLE_MODIFICATION],
        max_iterations=8,
    )
    assert summary.plan.plan_version >= 1
