"""Research Intelligence and Evidence Ledger schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ResearchMode = Literal["quick", "decision", "deep", "benchmark"]
SupportStatus = Literal[
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "CONTRADICTED",
    "UNVERIFIED",
    "INSUFFICIENT_EVIDENCE",
    # Legacy aliases
    "verified",
    "contradicted",
    "inferred",
    "stale",
]


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Research question or topic to investigate")
    mode: ResearchMode = Field(default="deep", description="Research depth mode")
    max_sources: int = Field(default=5, ge=1, le=20)


class SourceRecordSchema(BaseModel):
    id: str
    url: str
    title: str
    publisher: str
    source_type: str
    publication_date: str | None = None
    retrieved_at: datetime
    locator: str | None = None
    is_accessible: bool = True
    provenance: str = Field(default="live_web", description="live_web, stored_evidence, user_reference, simulated_mock")
    is_mock: bool = False
    content_hash: str | None = None
    reliability_tier: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceClaimSchema(BaseModel):
    id: str
    claim_text: str
    support_status: SupportStatus
    confidence_score: float
    confidence_rationale: str | None = None
    excerpt: str | None = None
    source_id: str
    source_url: str | None = None
    contrary_evidence: list[dict[str, Any]] = Field(default_factory=list)
    provenance: str = Field(default="live_web", description="live_web, stored_evidence, user_reference, simulated_mock")
    is_mock: bool = False
    content_hash: str | None = None
    reliability_tier: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ResearchResponse(BaseModel):
    job_id: str
    status: str
    query: str
    mode: ResearchMode
    plan: dict[str, Any]
    summary: dict[str, Any]
    sources: list[SourceRecordSchema]
    claims: list[EvidenceClaimSchema]

    model_config = ConfigDict(from_attributes=True)
