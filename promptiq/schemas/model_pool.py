"""Model Pool, Privacy, and Multi-Model Collaboration Schemas."""

from datetime import datetime
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

    training_policy: str = Field(..., description="e.g. human_review_for_training, no_training, opt_out")
    data_retention_days: int = Field(default=30)
    deletion_api_available: bool = Field(default=False)
    jurisdiction: str = Field(default="United States")
    allows_confidential_data: bool = Field(default=False)
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


class ExecutionStepRecord(BaseModel):
    """Audit record for an individual step in a multi-model collaboration workflow."""

    step_number: int
    role: LogicalModelRole
    provider: str
    model_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    quota_remaining: int | None = None
    verification_passed: bool = True
    findings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class MultiModelExecutionAuditRecord(BaseModel):
    """Immutable audit trail for a multi-model execution session."""

    workflow_id: str
    project_id: str
    task_id: str
    execution_profile: ExecutionProfile
    data_sensitivity: DataSensitivityLevel
    steps: list[ExecutionStepRecord] = Field(default_factory=list)
    consensus_status: str = Field(default="agreed", description="agreed, adjudicated, uncertainty_retained, deterministic_override")
    disagreement_details: dict[str, Any] | None = None
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    final_status: str = Field(default="SUCCESS", description="SUCCESS, FAILED, QUOTA_EXHAUSTED, POLICY_REJECTED")

    model_config = ConfigDict(from_attributes=True)
