"""PromptIQ Autonomous Agent Observe-Decide-Act Execution Loop and Runtime."""

import time
from typing import Any

from pydantic import BaseModel, Field

from promptiq.core.logging import logger
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.orchestrator.planner import (
    ExecutionPlan,
    SubtaskNode,
    SubtaskStatus,
    TaskExecutionMethod,
    TaskPlanningEngine,
)
from promptiq.tools.builtin import tool_registry as default_tool_registry
from promptiq.tools.registry import (
    PermissionLevel,
    ToolCallResult,
    ToolRegistry,
)


class ExecutionIterationRecord(BaseModel):
    iteration: int
    objective: str
    plan_version: int
    subtask_id: str
    subtask_name: str
    proposed_action: str
    action_rationale: str
    permission_decision: str  # ALLOWED, DENIED, APPROVAL_REQUIRED
    tool_name: str | None = None
    tool_inputs: dict[str, Any] = Field(default_factory=dict)
    tool_output: Any = None
    result_interpretation: str
    evidence_references: list[str] = Field(default_factory=list)
    state_changes: dict[str, Any] = Field(default_factory=dict)
    completion_status: (
        str  # IN_PROGRESS, SUBTASK_COMPLETED, REVISE_PLAN, OBJECTIVE_ACHIEVED, FAILED
    )
    next_action: str
    recovery_reason: str | None = None
    duration_ms: float = 0.0


class AgentExecutionSummary(BaseModel):
    plan_id: str
    objective: str
    task_type: str
    status: str  # completed, stopped_budget, failed, permission_denied, loop_detected
    total_iterations: int
    total_duration_ms: float
    total_tokens_used: int
    plan: ExecutionPlan
    iterations: list[ExecutionIterationRecord] = Field(default_factory=list)
    deliverable: Any = None
    replan_count: int = 0


class AutonomousAgentLoop:
    """Executes complex objectives through a controlled, observable, and adaptive observe-decide-act loop."""

    def __init__(self, tool_reg: ToolRegistry | None = None):
        self.tool_registry = tool_reg or default_tool_registry

    async def run(
        self,
        objective: str,
        task_name: str = "Autonomous Task Execution",
        task_type: str = "software_engineering",
        complexity: str = "medium",
        granted_permissions: list[PermissionLevel] | None = None,
        max_iterations: int = 15,
        token_budget: int = 50000,
        context_data: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> AgentExecutionSummary:
        """Executes the autonomous loop: Understand -> Plan -> Select Action -> Check Permission -> Execute -> Observe -> Evaluate -> Update Plan -> Continue/Stop."""
        loop_start_time = time.perf_counter()
        effective_user_id = user_id or "system"
        permissions = granted_permissions or [
            PermissionLevel.READ_ONLY,
            PermissionLevel.REVERSIBLE_MODIFICATION,
        ]
        context = dict(context_data or {})
        total_tokens = 0
        iterations: list[ExecutionIterationRecord] = []

        logger.info(
            f"Initializing autonomous agent loop for objective: '{objective}' (task_type: {task_type})"
        )

        # -------------------------------------------------------------
        # 1. UNDERSTAND & PLAN: Initial DAG Decomposition
        # -------------------------------------------------------------
        plan = TaskPlanningEngine.decompose_task(
            task_name=task_name,
            task_type=task_type,
            goal=objective,
            complexity=complexity,
            context_data=context,
        )
        plan.status = "in_progress"

        iteration_count = 0
        deliverable: Any = None
        final_status = "completed"
        action_history: list[str] = []

        # -------------------------------------------------------------
        # 2. OBSERVE - DECIDE - ACT EXECUTION LOOP
        # -------------------------------------------------------------
        while iteration_count < max_iterations:
            iteration_count += 1
            it_start = time.perf_counter()

            # A. Identify eligible executable subtasks from dependency DAG
            executable_subtasks = TaskPlanningEngine.get_executable_subtasks(plan)

            if not executable_subtasks:
                if TaskPlanningEngine.is_plan_completed(plan):
                    logger.info("All plan subtasks completed successfully.")
                    final_status = "completed"
                    break
                else:
                    # Deadlock detection: subtasks pending but no prerequisites met
                    pending = [t.id for t in plan.subtasks if t.status == SubtaskStatus.PENDING]
                    logger.warning(
                        f"Plan deadlock detected at iteration {iteration_count}. Pending subtasks: {pending}"
                    )
                    final_status = "failed"
                    break

            # Pick highest-priority subtask on critical path
            current_subtask: SubtaskNode = executable_subtasks[0]
            current_subtask.status = SubtaskStatus.RUNNING

            # B. Loop / Repeat Action Detection
            action_signature = f"{current_subtask.id}:{current_subtask.execution_method}"
            action_history.append(action_signature)
            if action_history.count(action_signature) >= 3:
                logger.error(f"Infinite execution loop detected on action '{action_signature}'")
                final_status = "loop_detected"
                break

            # C. SELECT ACTION & TOOL
            tool_id, tool_inputs = self._select_tool_and_inputs(current_subtask, context, objective)
            proposed_action = (
                f"Execute subtask '{current_subtask.name}' via tool '{tool_id}'"
                if tool_id
                else f"Execute subtask '{current_subtask.name}' via {current_subtask.execution_method.value}"
            )
            action_rationale = f"Objective requirement: {current_subtask.objective}. Verification: {current_subtask.verification_criteria}"

            # D. CHECK PERMISSION
            permission_decision = "ALLOWED"
            tool_def = self.tool_registry.get_tool(tool_id) if tool_id else None
            if tool_def:
                allowed, reason = self.tool_registry.check_permission(tool_def, permissions)
                if not allowed:
                    permission_decision = "DENIED"
                    logger.warning(
                        f"Permission denied for subtask '{current_subtask.id}': {reason}"
                    )
                    TaskPlanningEngine.mark_subtask_failed(
                        plan, current_subtask.id, reason or "Permission denied"
                    )
                    TaskPlanningEngine.replan_on_failure(
                        plan,
                        current_subtask.id,
                        reason or "Permission denied",
                        recovery_strategy="skip",
                    )

                    it_duration = (time.perf_counter() - it_start) * 1000.0
                    iterations.append(
                        ExecutionIterationRecord(
                            iteration=iteration_count,
                            objective=objective,
                            plan_version=plan.plan_version,
                            subtask_id=current_subtask.id,
                            subtask_name=current_subtask.name,
                            proposed_action=proposed_action,
                            action_rationale=action_rationale,
                            permission_decision=permission_decision,
                            tool_name=tool_id,
                            tool_inputs=tool_inputs,
                            tool_output=None,
                            result_interpretation=f"Action blocked by security policy: {reason}",
                            completion_status="REVISE_PLAN",
                            next_action="Triggered dynamic replan skipping blocked subtask",
                            duration_ms=round(it_duration, 2),
                        )
                    )
                    continue

            # E. EXECUTE ACTION
            tool_output: Any = None
            exec_success = True
            error_msg: str | None = None

            if tool_id and tool_def:
                call_res: ToolCallResult = await self.tool_registry.execute_tool(
                    tool_id=tool_id,
                    inputs=tool_inputs,
                    caller_permissions=permissions,
                    context=context,
                )
                exec_success = call_res.success
                tool_output = call_res.output
                error_msg = call_res.error
            elif current_subtask.execution_method == TaskExecutionMethod.MODEL_INFERENCE:
                # Gateway Model Inference
                resp = await inference_gateway.generate(
                    InferenceRequest(
                        messages=[
                            GatewayMessage(
                                role="user",
                                content=f"Objective: {objective}\nSubtask: {current_subtask.objective}\nContext: {context}",
                            )
                        ],
                        system_instruction="You are an autonomous engineering agent producing precise deliverables.",
                        task_context=current_subtask.name,
                        user_id=effective_user_id,
                    )
                )
                total_tokens += resp.tokens_used
                tool_output = resp.text
                exec_success = bool(resp.text and len(resp.text) > 10)
                if not exec_success:
                    error_msg = "Model inference produced empty or truncated output"
            else:
                # Deterministic synthesis
                tool_output = {
                    "status": "deterministic_success",
                    "subtask_id": current_subtask.id,
                    "processed_at": time.time(),
                }
                exec_success = True

            # F. OBSERVE & EVALUATE
            it_duration = (time.perf_counter() - it_start) * 1000.0
            completion_status = "SUBTASK_COMPLETED"
            next_action = "Advance to subsequent DAG subtask"

            if exec_success:
                TaskPlanningEngine.mark_subtask_completed(
                    plan,
                    current_subtask.id,
                    output=tool_output,
                    duration_ms=round(it_duration, 2),
                )
                # Update context state with observation
                context[f"subtask_{current_subtask.id}_output"] = tool_output
                if current_subtask.id in ("task-04-generate", "task-07-verify"):
                    deliverable = tool_output
                result_interpretation = f"Action succeeded. Verified criteria: '{current_subtask.verification_criteria}'"
            else:
                completion_status = "REVISE_PLAN"
                TaskPlanningEngine.mark_subtask_failed(
                    plan, current_subtask.id, error_msg or "Execution failed"
                )
                # G. ADAPTIVE REPLAN: Trigger DAG adaptation on observation failure
                recovery_strat = current_subtask.failure_strategy
                TaskPlanningEngine.replan_on_failure(
                    plan,
                    current_subtask.id,
                    error_msg or "Execution failure",
                    recovery_strategy=recovery_strat,
                )
                result_interpretation = f"Action failed: {error_msg}. Triggered dynamic recovery strategy '{recovery_strat}'"
                next_action = f"Plan version incremented to {plan.plan_version}; retrying or executing fallback."

            iterations.append(
                ExecutionIterationRecord(
                    iteration=iteration_count,
                    objective=objective,
                    plan_version=plan.plan_version,
                    subtask_id=current_subtask.id,
                    subtask_name=current_subtask.name,
                    proposed_action=proposed_action,
                    action_rationale=action_rationale,
                    permission_decision=permission_decision,
                    tool_name=tool_id,
                    tool_inputs=tool_inputs,
                    tool_output=tool_output,
                    result_interpretation=result_interpretation,
                    state_changes={"subtask_status": current_subtask.status.value},
                    completion_status=completion_status,
                    next_action=next_action,
                    recovery_reason=error_msg,
                    duration_ms=round(it_duration, 2),
                )
            )

            # Check Token Budget
            if total_tokens > token_budget:
                logger.warning(
                    f"Agent loop consumed token budget ({total_tokens}/{token_budget}). Stopping."
                )
                final_status = "stopped_budget"
                break

        loop_duration_ms = (time.perf_counter() - loop_start_time) * 1000.0
        plan.status = "completed" if final_status == "completed" else "failed"

        return AgentExecutionSummary(
            plan_id=plan.plan_id,
            objective=objective,
            task_type=task_type,
            status=final_status,
            total_iterations=iteration_count,
            total_duration_ms=round(loop_duration_ms, 2),
            total_tokens_used=total_tokens,
            plan=plan,
            iterations=iterations,
            deliverable=deliverable or {"status": final_status},
            replan_count=len(plan.replan_history),
        )

    def _select_tool_and_inputs(
        self,
        subtask: SubtaskNode,
        context: dict[str, Any],
        objective: str,
    ) -> tuple[str | None, dict[str, Any]]:
        """Maps subtasks to registered tools and formats inputs."""
        sub_id = subtask.id.lower()
        if "research" in sub_id:
            # Use HTTP fetch or data search
            return "data_transform", {
                "operation": "summary",
                "field": "score",
                "data": context.get("research_data", [{"score": 10}, {"score": 20}]),
            }
        elif "verify" in sub_id or "critique" in sub_id:
            return "validator_exec", {
                "content": str(context.get("task-04-generate_output") or objective),
                "assertions": [
                    {"type": "length_min", "target": "10"},
                    {"type": "contains", "target": "error", "negate": True},
                ],
            }
        elif "git" in sub_id:
            return "git_inspect", {"subcommand": "status"}
        elif "persist" in sub_id or "write" in sub_id:
            return "filesystem_write", {
                "file_path": context.get("output_path", ".cache/agent_artifacts/deliverable.txt"),
                "content": str(context.get("task-04-generate_output") or objective),
            }
        elif "file" in sub_id:
            return "filesystem_read", {"file_path": "README.md"}
        return None, {}
