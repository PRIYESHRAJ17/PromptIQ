"""PromptIQ Acceptance Framework Schemas and Execution States.

Defines the formal state machine, execution modes, acceptance criteria,
artifact bindings, and comprehensive audit trail models.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionState(StrEnum):
    """Explicit lifecycle execution states for acceptance verification."""

    STEP_EXECUTED = "STEP_EXECUTED"
    STEP_VALIDATED = "STEP_VALIDATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NEEDS_REVISION = "NEEDS_REVISION"
    REVISION_IN_PROGRESS = "REVISION_IN_PROGRESS"
    REVISION_VERIFIED = "REVISION_VERIFIED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    SUCCESS_FULLY_VERIFIED = "SUCCESS_FULLY_VERIFIED"


class ExecutionMode(StrEnum):
    """Categorization of test execution and evaluation provenance."""

    MOCK = "MOCK"
    SYNTHETIC = "SYNTHETIC"
    DETERMINISTIC = "DETERMINISTIC"
    LIVE_PROVIDER = "LIVE_PROVIDER"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class SourceRetrievalClassification(StrEnum):
    """Rigorous classification of research evidence source retrieval."""

    LIVE_RETRIEVED = "LIVE_RETRIEVED"
    USER_PROVIDED = "USER_PROVIDED"
    STORED_EVIDENCE = "STORED_EVIDENCE"
    SIMULATED = "SIMULATED"
    FAILED = "FAILED"
    UNVERIFIED = "UNVERIFIED"


class TargetProvenanceStatus(StrEnum):
    """Evidence status for target host capabilities and limits."""

    OFFICIALLY_VERIFIED = "OFFICIALLY_VERIFIED"
    PROVIDER_DOCUMENTED_VERSION_DEPENDENT = "PROVIDER_DOCUMENTED_VERSION_DEPENDENT"
    EMPIRICALLY_TESTED = "EMPIRICALLY_TESTED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"


class IntegrationStatus(StrEnum):
    """Maturity and verification level for product surfaces."""

    IMPLEMENTED = "IMPLEMENTED"
    LOCAL_INTEGRATION_TESTED = "LOCAL_INTEGRATION_TESTED"
    EXTERNAL_CLIENT_TESTED = "EXTERNAL_CLIENT_TESTED"
    LIVE_SERVICE_VERIFIED = "LIVE_SERVICE_VERIFIED"
    BLOCKED = "BLOCKED"
    UNVERIFIED = "UNVERIFIED"


class StepRecord(BaseModel):
    """Detailed audit log for an individual execution step."""

    step_name: str
    state: ExecutionState
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = Field(default_factory=dict)
    validation_notes: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class StateTransitionRecord(BaseModel):
    """Immutable audit record of a state transition."""

    transition_id: str = Field(default_factory=lambda: f"TRANS-{uuid.uuid4().hex[:8]}")
    from_state: ExecutionState
    to_state: ExecutionState
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reason: str
    step_context: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AcceptanceCriterion(BaseModel):
    """Measurable contract condition that must be verified for release."""

    id: str
    description: str
    is_mandatory: bool = True
    satisfied: bool = False
    evidence: str | None = None
    evaluated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ArtifactBinding(BaseModel):
    """Cryptographic binding linking an inspection to an exact artifact version."""

    artifact_id: str
    artifact_type: str
    content_hash: str  # SHA-256
    version: int = 1
    persisted: bool = False
    retrievable: bool = False
    byte_size: int = 0

    model_config = ConfigDict(from_attributes=True)


class AutopsyInspectionRecord(BaseModel):
    """Immutable audit record of a Prompt Autopsy diagnosis phase."""

    run_id: str = Field(default_factory=lambda: f"AUT-{uuid.uuid4().hex[:8]}")
    phase: str = "initial"  # initial, interim, final
    artifact_id: str
    artifact_hash: str
    verdict: str
    findings_count: int = 0
    findings: list[dict[str, Any]] = Field(default_factory=list)
    quality_scores: dict[str, float] = Field(default_factory=dict)
    inspected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class RevisionEventRecord(BaseModel):
    """Immutable audit record of an artifact revision event."""

    revision_id: str = Field(default_factory=lambda: f"REV-{uuid.uuid4().hex[:8]}")
    previous_artifact_id: str
    previous_artifact_hash: str
    revised_artifact_id: str
    revised_artifact_hash: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    changes_summary: str = ""

    model_config = ConfigDict(from_attributes=True)


class FindingResolutionEvent(BaseModel):
    """Formal resolution event binding an original finding to the exact revised artifact hash."""

    resolution_id: str = Field(default_factory=lambda: f"RES-{uuid.uuid4().hex[:8]}")
    finding_id: str
    original_category: str
    original_severity: str
    revised_artifact_hash: str
    status: str = "resolved"  # resolved, partially_resolved, rejected_with_reason, unresolved
    resolution_evidence: str
    verification_reason: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class WarningRecord(BaseModel):
    """Structured warning derived from an unresolved non-blocking advisory finding."""

    warning_id: str = Field(default_factory=lambda: f"WARN-{uuid.uuid4().hex[:8]}")
    finding_id: str
    severity: str
    category: str
    finding_text: str
    consequence: str
    recommendation: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class ScenarioAuditTrace(BaseModel):
    """Complete, versioned audit trace for an acceptance scenario."""

    scenario_id: str
    category: str
    input_summary: dict[str, Any]
    execution_mode: ExecutionMode
    current_state: ExecutionState
    terminal_state: ExecutionState | None = None
    steps: list[StepRecord] = Field(default_factory=list)
    transitions: list[StateTransitionRecord] = Field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    artifact_bindings: list[ArtifactBinding] = Field(default_factory=list)
    initial_autopsy: AutopsyInspectionRecord | None = None
    revision_events: list[RevisionEventRecord] = Field(default_factory=list)
    resolution_events: list[FindingResolutionEvent] = Field(default_factory=list)
    final_autopsy: AutopsyInspectionRecord | None = None
    autopsy_findings: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_findings: list[dict[str, Any]] = Field(default_factory=list)
    evaluation_records: list[dict[str, Any]] = Field(default_factory=list)
    warning_records: list[WarningRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    execution_metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class AcceptanceSuiteSummary(BaseModel):
    """Machine-verifiable summary across all executed scenarios."""

    runner_version: str = "3.0.0"
    execution_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_scenarios: int = 0
    fully_verified_count: int = 0
    completed_with_warnings_count: int = 0
    blocked_count: int = 0
    failed_count: int = 0
    overall_verdict: str  # PASS, CONDITIONAL_PASS, BLOCKED, FAILED
    scenarios: list[ScenarioAuditTrace] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
