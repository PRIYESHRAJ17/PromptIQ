"""PromptIQ Hierarchical Task Planning Engine and Bounded Execution-Intelligence Loop."""

import time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskExecutionMethod(StrEnum):
    DETERMINISTIC_CODE = "deterministic_code"
    MODEL_INFERENCE = "model_inference"
    MULTI_MODEL_COLLABORATION = "multi_model_collaboration"
    RESEARCH_RETRIEVAL = "research_retrieval"
    VALIDATOR_VERIFICATION = "validator_verification"


class SubtaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SubtaskNode(BaseModel):
    id: str
    name: str
    objective: str
    required_context: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected_output_type: str = "json"  # json, text, code, artifact
    dependencies: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    execution_method: TaskExecutionMethod = TaskExecutionMethod.MODEL_INFERENCE
    verification_criteria: str
    failure_strategy: str = "retry_with_backoff"  # fail_fast, retry_with_backoff, fallback, skip
    status: SubtaskStatus = SubtaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 2
    output: Any = None
    execution_duration_ms: float = 0.0
    error_message: str | None = None


class ExecutionPlan(BaseModel):
    plan_id: str
    task_name: str
    task_type: str
    complexity: str
    critical_path: list[str] = Field(default_factory=list)
    subtasks: list[SubtaskNode] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    status: str = "initialized"  # initialized, in_progress, completed, failed


class ExecutionLoopStage(StrEnum):
    UNDERSTAND = "understand"
    DISCOVER = "discover"
    SPECIFY = "specify"
    PLAN = "plan"
    EXECUTE = "execute"
    INSPECT = "inspect"
    CRITIQUE = "critique"
    REVISE = "revise"
    VERIFY = "verify"
    DELIVER = "deliver"
    REMEMBER = "remember"


class TaskPlanningEngine:
    """Decomposes complex tasks into validated dependency DAGs and plans execution."""

    @classmethod
    def decompose_task(
        cls,
        task_name: str,
        task_type: str,
        goal: str,
        complexity: str = "medium",
        constraints: list[str] | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> ExecutionPlan:
        """Constructs a hierarchical DAG execution plan tailored to task type and complexity."""
        plan_id = f"plan-{int(time.time() * 1000)}"
        subtasks: list[SubtaskNode] = []

        # 1. Understanding & Intent Decomposition
        subtasks.append(
            SubtaskNode(
                id="task-01-intent",
                name="Intent & Boundary Analysis",
                objective=f"Analyze objective '{goal}' and extract explicit/implicit constraints",
                dependencies=[],
                execution_method=TaskExecutionMethod.DETERMINISTIC_CODE,
                verification_criteria="Non-empty primary objective and identified non-negotiable boundaries",
            )
        )

        # 2. Research & Grounding (if research or complex engineering)
        if task_type in ("research_intelligence", "software_engineering", "ai_agent_development") or complexity in ("high", "extreme"):
            subtasks.append(
                SubtaskNode(
                    id="task-02-research",
                    name="Evidence & Domain Research",
                    objective="Retrieve domain evidence, technical references, or API constraints",
                    dependencies=["task-01-intent"],
                    execution_method=TaskExecutionMethod.RESEARCH_RETRIEVAL,
                    verification_criteria="Evidence ledger populated with valid source references or simulated fallback markers",
                )
            )

        # 3. Specification & Constitution Alignment
        deps_for_spec = ["task-02-research"] if any(t.id == "task-02-research" for t in subtasks) else ["task-01-intent"]
        subtasks.append(
            SubtaskNode(
                id="task-03-specification",
                name="Project Specification & Constitution",
                objective="Synthesize typed PPS specification with explicit requirement IDs",
                dependencies=deps_for_spec,
                execution_method=TaskExecutionMethod.DETERMINISTIC_CODE,
                verification_criteria="Valid PPS v2.0 schema with all P0/P1 requirements bound",
            )
        )

        # 4. Core Synthesis / Generation
        subtasks.append(
            SubtaskNode(
                id="task-04-generate",
                name="Deliverable Synthesis",
                objective="Compile target instructions or synthesize operational deliverable",
                dependencies=["task-03-specification"],
                execution_method=TaskExecutionMethod.MODEL_INFERENCE,
                verification_criteria="Deliverable length > 100 bytes and passes format assertions",
            )
        )

        # 5. Prompt Autopsy & Adversarial Critique
        subtasks.append(
            SubtaskNode(
                id="task-05-critique",
                name="Prompt Autopsy & Inspection",
                objective="Inspect synthesized deliverable across 21 failure modes",
                dependencies=["task-04-generate"],
                execution_method=TaskExecutionMethod.DETERMINISTIC_CODE,
                verification_criteria="Autopsy diagnostic report produced with severity-calibrated findings",
            )
        )

        # 6. Revision Loop (Conditional on findings)
        subtasks.append(
            SubtaskNode(
                id="task-06-revise",
                name="Targeted Finding Revision",
                objective="Remediate critical and high-severity autopsy findings",
                dependencies=["task-05-critique"],
                execution_method=TaskExecutionMethod.MODEL_INFERENCE,
                verification_criteria="All critical findings resolved or documented with justification",
                failure_strategy="skip",
            )
        )

        # 7. Final Verification & Test Lab
        subtasks.append(
            SubtaskNode(
                id="task-07-verify",
                name="Test Lab Verification & Assertion Gate",
                objective="Execute deterministic assertions and test cases against deliverable",
                dependencies=["task-06-revise"],
                execution_method=TaskExecutionMethod.VALIDATOR_VERIFICATION,
                verification_criteria="Passing score >= threshold and zero invariant violations",
            )
        )

        # 8. Memory & Checkpoint Persistence
        subtasks.append(
            SubtaskNode(
                id="task-08-persist",
                name="State & Memory Persistence",
                objective="Persist artifacts, update project memory, and commit execution provenance",
                dependencies=["task-07-verify"],
                execution_method=TaskExecutionMethod.DETERMINISTIC_CODE,
                verification_criteria="Artifacts stored with verified SHA-256 hashes and DB rows",
            )
        )

        # Compute Critical Path (Longest dependency chain)
        critical_path = [t.id for t in subtasks]

        return ExecutionPlan(
            plan_id=plan_id,
            task_name=task_name,
            task_type=task_type,
            complexity=complexity,
            critical_path=critical_path,
            subtasks=subtasks,
            status="initialized",
        )

    @classmethod
    def get_executable_subtasks(cls, plan: ExecutionPlan) -> list[SubtaskNode]:
        """Identifies subtasks whose dependencies have all completed successfully."""
        completed_ids = {t.id for t in plan.subtasks if t.status == SubtaskStatus.COMPLETED}
        executable: list[SubtaskNode] = []

        for subtask in plan.subtasks:
            if subtask.status == SubtaskStatus.PENDING:
                if all(dep in completed_ids for dep in subtask.dependencies):
                    executable.append(subtask)

        return executable
