"""Model Pool, Privacy, and Multi-Model Collaboration Schemas."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EligibilityState(StrEnum):
    """Formal eligibility states for model registry and gateway enforcement."""

    VERIFIED_ELIGIBLE = "VERIFIED_ELIGIBLE"
    CONDITIONALLY_ELIGIBLE = "CONDITIONALLY_ELIGIBLE"
    UNVERIFIED = "UNVERIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INELIGIBLE_TERMS = "INELIGIBLE_TERMS"
    INELIGIBLE_PRIVACY = "INELIGIBLE_PRIVACY"
    INELIGIBLE_PAID = "INELIGIBLE_PAID"
    INELIGIBLE_BILLING = "INELIGIBLE_BILLING"
    INELIGIBLE_AUDIENCE = "INELIGIBLE_AUDIENCE"
    RETIRED = "RETIRED"
    UNAVAILABLE = "UNAVAILABLE"


class DataSensitivityLevel(StrEnum):
    """Data sensitivity levels for privacy-aware routing."""

    PUBLIC = "PUBLIC"
    GENERAL = "GENERAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class LogicalModelRole(StrEnum):
    """Specialized functional roles in the PromptIQ multi-model architecture."""

    ORCHESTRATOR = "ORCHESTRATOR"
    REASONING = "REASONING"
    FAST = "FAST"
    RESEARCH = "RESEARCH"
    PROMPT_ENGINEER = "PROMPT_ENGINEER"
    CRITIC = "CRITIC"
    VERIFIER = "VERIFIER"


class ExecutionProfile(StrEnum):
    """Collaboration execution profiles balancing speed, cost, and rigor."""

    QUICK = "QUICK"
    STANDARD = "STANDARD"
    DEEP = "DEEP"
    HIGH_RISK = "HIGH_RISK"


class ProviderPrivacyCard(BaseModel):
    """Provider privacy terms, training policy, and data handling guarantees."""

    training_policy: str = Field(
        ..., description="e.g. human_review_for_training, no_training, opt_out"
    )
    data_retention_days: int = Field(default=30)
    deletion_api_available: bool = Field(default=False)
    jurisdiction: str = Field(default="United States")
    allows_confidential_data: bool = Field(default=False)
    min_operator_age: int = Field(default=18)
    allows_minors: bool = Field(default=False)
    audience_restrictions: str | None = None
    privacy_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ModelCapabilities(BaseModel):
    """Detailed model capability flags."""

    reasoning: bool = True
    coding: bool = True
    structured_output: bool = True
    tools: bool = True
    vision: bool = False
    long_context: bool = False

    model_config = ConfigDict(from_attributes=True)


class ModelRateLimits(BaseModel):
    """Granular model-specific quota ceilings."""

    rpm: int = 30
    rpd: int = 1000
    tpm: int = 10000
    tpd: int = 100000

    model_config = ConfigDict(from_attributes=True)


class ModelPoolRecord(BaseModel):
    """Complete record for a model in the centrally managed zero-price pool."""

    id: str
    provider: str
    model_id: str
    name: str
    model_family: str
    version: str
    eligibility_state: EligibilityState
    capabilities: ModelCapabilities
    context_window: int
    output_limit: int
    rate_limits: ModelRateLimits
    privacy_card: ProviderPrivacyCard
    max_allowed_data_sensitivity: DataSensitivityLevel = DataSensitivityLevel.GENERAL
    cost_input_per_token: float = 0.0
    cost_output_per_token: float = 0.0
    is_zero_price: bool = True
    benchmark_scores: dict[str, float] = Field(default_factory=dict)
    composite_score: float = 0.0
    eligible_use_cases: list[str] = Field(default_factory=list)
    ineligible_use_cases: list[str] = Field(default_factory=list)
    verification_date: str
    verification_evidence: str
    source_url: str

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionStatus(StrEnum):
    """Accurate lifecycle execution states for multi-model collaboration workflows."""

    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    RATE_LIMITED = "RATE_LIMITED"
    FAILED = "FAILED"
    RESUMABLE = "RESUMABLE"
    PARTIALLY_COMPLETED_RATE_LIMITED = "PARTIALLY_COMPLETED_RATE_LIMITED"
    SUCCESS = "SUCCESS"


class StageExecutionStatus(StrEnum):
    """Independent status for an individual stage in a multi-model collaboration."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED = "VERIFIED"
    RATE_LIMITED = "RATE_LIMITED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    INCOMPLETE = "INCOMPLETE"


class ExecutionStepRecord(BaseModel):
    """Audit record for an individual step in a multi-model collaboration workflow."""

    step_number: int
    role: LogicalModelRole
    provider: str = "internal"
    model_id: str | None = None
    timestamp: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    latency_ms: float | None = 0.0
    input_tokens: int | None = 0
    output_tokens: int | None = 0
    quota_remaining: int | None = None
    verification_passed: bool = True
    findings: list[str] = Field(default_factory=list)
    request_id: str | None = None
    http_status: int | None = None
    stage: str | None = None
    outcome_status: str = "VERIFIED"
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class MultiModelExecutionAuditRecord(BaseModel):
    """Immutable audit trail for a multi-model execution session."""

    workflow_id: str
    parent_workflow_id: str | None = None
    project_id: str = "proj-default"
    task_id: str = "task-default"
    execution_profile: ExecutionProfile = ExecutionProfile.STANDARD
    data_sensitivity: DataSensitivityLevel = DataSensitivityLevel.GENERAL
    steps: list[ExecutionStepRecord] = Field(default_factory=list)
    consensus_status: str = Field(
        default="agreed",
        description="agreed, adjudicated, uncertainty_retained, deterministic_override, same_family_intra_provider_disclosed",
    )
    disagreement_details: dict[str, Any] | None = None
    total_latency_ms: float | None = 0.0
    total_tokens: int | None = 0
    final_status: str = Field(
        default="COMPLETED",
        description="COMPLETED, PARTIALLY_COMPLETED, RATE_LIMITED, FAILED, RESUMABLE, PARTIALLY_COMPLETED_RATE_LIMITED, SUCCESS",
    )
    stage_statuses: dict[str, str] = Field(default_factory=dict)
    generator_provider: str | None = None
    generator_model_id: str | None = None
    critic_provider: str | None = None
    critic_model_id: str | None = None
    is_multi_model: bool = True
    is_multi_provider: bool = False
    is_multi_family: bool = False
    model_diversity_rating: str = "MULTI_MODEL_SAME_FAMILY_SAME_PROVIDER"
    deterministic_verification_passed: bool | None = True
    failure_occurred: bool = False
    fallback_occurred: bool = False
    initial_artifact: str | None = None
    critic_review: str | None = None
    revised_artifact: str | None = None
    resolution_breakdown: dict[str, list[str]] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
