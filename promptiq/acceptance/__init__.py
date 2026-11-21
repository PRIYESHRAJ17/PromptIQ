"""PromptIQ Acceptance Framework package."""

from promptiq.acceptance.runner import (
    run_all_acceptance_scenarios,
    run_scenario_1_software,
    run_scenario_2_research,
    run_scenario_3_agent,
    run_scenario_4_business,
    run_scenario_5_prompt_improvement,
    setup_test_workspace_and_user,
)
from promptiq.acceptance.state_machine import (
    AcceptanceError,
    AcceptanceStateMachine,
    ArtifactBindingError,
    GateValidationError,
    InvalidTransitionError,
)
from promptiq.schemas.acceptance import (
    AcceptanceCriterion,
    AcceptanceSuiteSummary,
    ArtifactBinding,
    ExecutionMode,
    ExecutionState,
    IntegrationStatus,
    ScenarioAuditTrace,
    SourceRetrievalClassification,
    StateTransitionRecord,
    StepRecord,
    TargetProvenanceStatus,
)

__all__ = [
    "AcceptanceCriterion",
    "AcceptanceError",
    "AcceptanceStateMachine",
    "AcceptanceSuiteSummary",
    "ArtifactBinding",
    "ArtifactBindingError",
    "ExecutionMode",
    "ExecutionState",
    "GateValidationError",
    "IntegrationStatus",
    "InvalidTransitionError",
    "ScenarioAuditTrace",
    "SourceRetrievalClassification",
    "StateTransitionRecord",
    "StepRecord",
    "TargetProvenanceStatus",
    "run_all_acceptance_scenarios",
    "run_scenario_1_software",
    "run_scenario_2_research",
    "run_scenario_3_agent",
    "run_scenario_4_business",
    "run_scenario_5_prompt_improvement",
    "setup_test_workspace_and_user",
]
