"""PromptIQ Prompt Specification (PPS v2.0.0) intermediate representation schema."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IntentSchema(BaseModel):
    task_type: str = "software_project"
    primary_objective: str
    target_audience: str = "developers"
    success_criteria: list[str] = Field(default_factory=list)


class TargetProfileSchema(BaseModel):
    host: str = Field(
        ..., description="e.g. google-antigravity, claude-code, cursor, openai-codex, gemini-cli"
    )
    provider: str = Field(..., description="e.g. google, anthropic, openai")
    model_id: str = Field(..., description="e.g. gemini-3.8-flash, claude-3-7-sonnet, gpt-4o")
    route: str = Field(default="hosted_adapter", description="Access route")
    runtime_version: str | None = None
    tools_available: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class DeliverableItem(BaseModel):
    path: str
    format: str = "text/markdown"
    description: str
    originating_requirement_ids: list[str] = Field(default_factory=list)


class OutputContractSchema(BaseModel):
    format: str = "markdown"
    sections_required: list[str] = Field(default_factory=list)
    rules_and_invariants: list[str] = Field(default_factory=list)
    manifest_required: bool = False


class RoleAndResponsibilities(BaseModel):
    role_title: str
    responsibilities: list[str] = Field(default_factory=list)
    non_responsibilities: list[str] = Field(default_factory=list)


class InputVariableSchema(BaseModel):
    name: str
    var_type: str = "string"
    description: str
    required: bool = True
    default: Any = None


class ExpectedOutputSchema(BaseModel):
    primary_deliverable: str
    format: str = "markdown"
    sections: list[str] = Field(default_factory=list)
    schema_definition: dict[str, Any] | None = None


class BehaviorRulesSchema(BaseModel):
    preservation_rules: list[str] = Field(default_factory=list)
    prohibitions: list[str] = Field(default_factory=list)
    operational_guidelines: list[str] = Field(default_factory=list)


class SecurityPrivacySchema(BaseModel):
    tenant_isolation_required: bool = True
    zero_key_storage: bool = True
    secret_leakage_prevention: bool = True
    sanitization_rules: list[str] = Field(default_factory=list)


class FailureHandlingSchema(BaseModel):
    fallback_action: str = "halt_and_report"
    escalation_conditions: list[str] = Field(default_factory=list)
    retry_policy: dict[str, Any] = Field(default_factory=dict)


class ResearchReferenceSchema(BaseModel):
    citations: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ledger_ref: str | None = None


class AcceptanceCriteriaSchema(BaseModel):
    items: list[str] = Field(default_factory=list)
    test_harness: str | None = None


class PromptSpecSchema(BaseModel):
    """The canonical, strongly-typed intermediate representation (PPS v2.1.0)."""

    spec_version: str = "2.1.0"
    project_id: str
    constitution_version: int
    intent: IntentSchema
    target_profile: TargetProfileSchema
    requirements: list[dict[str, Any]] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    tools_and_permissions: dict[str, Any] = Field(default_factory=dict)
    workflow_phases: list[dict[str, Any]] = Field(default_factory=list)
    deliverables: list[DeliverableItem] = Field(default_factory=list)
    output_contract: OutputContractSchema
    validation_plan: dict[str, Any] = Field(default_factory=dict)
    provenance_trail: dict[str, Any] = Field(default_factory=dict)

    # v2.0.0 Rich Structured Sections
    role_and_responsibilities: RoleAndResponsibilities | None = None
    input_variables: list[InputVariableSchema] = Field(default_factory=list)
    expected_output: ExpectedOutputSchema | None = None
    behavior_rules: BehaviorRulesSchema | None = None
    security_and_privacy: SecurityPrivacySchema | None = None
    failure_handling: FailureHandlingSchema | None = None
    research_references: ResearchReferenceSchema | None = None
    acceptance_criteria: AcceptanceCriteriaSchema | None = None

    model_config = ConfigDict(from_attributes=True)

    def validate_completeness(self) -> list[str]:
        """Validates that all foundational fields required for compilation are present and non-empty."""
        gaps: list[str] = []
        if not self.intent.primary_objective.strip():
            gaps.append("Primary objective is missing in intent.")
        if not self.target_profile.host:
            gaps.append("Target profile host is required.")
        if not self.requirements:
            gaps.append("No requirements provided in specification.")
        if not self.output_contract.sections_required:
            gaps.append("Output contract must specify required sections.")
        if self.security_and_privacy and not self.security_and_privacy.tenant_isolation_required:
            gaps.append("Tenant isolation must be enforced.")
        return gaps

    def to_normalized_dict(self) -> dict[str, Any]:
        """Returns a canonical, sorted dictionary representation suitable for deterministic hashing."""
        raw = self.model_dump(mode="json")
        return raw

    def to_deterministic_hash(self) -> str:
        """Computes a SHA-256 fingerprint of the normalized specification."""
        normalized_str = json.dumps(
            self.to_normalized_dict(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()
