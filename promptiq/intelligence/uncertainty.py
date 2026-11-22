"""PromptIQ Uncertainty Management, Calibration, and Epistemic Status Ledger."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EpistemicStatus(StrEnum):
    VERIFIED_FACT = "verified_fact"
    SOURCE_SUPPORTED_CLAIM = "source_supported_claim"
    MODEL_INTERPRETATION = "model_interpretation"
    INFERENCE = "inference"
    ASSUMPTION = "assumption"
    PREDICTION = "prediction"
    UNVERIFIED_STATEMENT = "unverified_statement"


class ConfidenceTier(StrEnum):
    PROVEN = "proven"  # 0.95 - 1.00: Cryptographically or deterministically verified
    HIGH = "high"  # 0.80 - 0.94: Supported by authoritative primary sources
    MEDIUM = "medium"  # 0.60 - 0.79: Plausible inference or secondary source
    LOW = "low"  # 0.40 - 0.59: Unverified assumption or model guess
    SPECULATIVE = "speculative"  # 0.00 - 0.39: Lacks evidence, needs clarification


class CalibratedClaim(BaseModel):
    id: str
    statement: str
    status: EpistemicStatus
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_tier: ConfidenceTier
    calibration_basis: str
    evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verified_by: str | None = None


class UncertaintyTracker:
    """Manages statement classification, confidence calibration, and epistemic tracking."""

    @staticmethod
    def calibrate_confidence(score: float) -> ConfidenceTier:
        """Assigns documented confidence tier based on calibrated numeric score."""
        if score >= 0.95:
            return ConfidenceTier.PROVEN
        elif score >= 0.80:
            return ConfidenceTier.HIGH
        elif score >= 0.60:
            return ConfidenceTier.MEDIUM
        elif score >= 0.40:
            return ConfidenceTier.LOW
        else:
            return ConfidenceTier.SPECULATIVE

    @classmethod
    def register_claim(
        cls,
        claim_id: str,
        statement: str,
        status: EpistemicStatus,
        confidence: float,
        calibration_basis: str,
        evidence_ids: list[str] | None = None,
        contradicting_ids: list[str] | None = None,
        verified_by: str | None = None,
    ) -> CalibratedClaim:
        """Registers a claim with strict epistemic status and calibration basis."""
        tier = cls.calibrate_confidence(confidence)
        return CalibratedClaim(
            id=claim_id,
            statement=statement,
            status=status,
            confidence=max(0.0, min(1.0, confidence)),
            confidence_tier=tier,
            calibration_basis=calibration_basis,
            evidence_ids=evidence_ids or [],
            contradicting_evidence_ids=contradicting_ids or [],
            verified_by=verified_by,
        )

    @classmethod
    def assess_uncertainty_action(cls, claim: CalibratedClaim) -> str:
        """Recommends action when uncertainty is high or ungrounded."""
        if claim.status in (EpistemicStatus.VERIFIED_FACT, EpistemicStatus.SOURCE_SUPPORTED_CLAIM):
            return "PROCEED: Claim is grounded and verified."
        elif claim.confidence < 0.60:
            if claim.contradicting_evidence_ids:
                return "RESOLVE_CONTRADICTION: Conflicting evidence exists. Must evaluate conflicting sources."
            return "SEEK_EVIDENCE_OR_CLARIFY: Uncertainty exceeds threshold. Prompt user or conduct research."
        elif claim.status == EpistemicStatus.ASSUMPTION:
            return "DOCUMENT_ASSUMPTION: Record assumption with clear provenance and allow user override."
        else:
            return "QUALIFY_STATEMENT: Present finding with explicit uncertainty disclaimer."
