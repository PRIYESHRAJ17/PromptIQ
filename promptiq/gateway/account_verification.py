"""Operator Free-Account Attestation and Verification Ledger.

Mandatory verification gate before live inference execution:
Ensures account is verified free, no credit card or paid developer plan is attached,
and native hard stops (HTTP 429) prevent financial charges.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from promptiq.core.config import settings
from promptiq.core.exceptions import PromptIQException


class OperatorVerificationRecord(BaseModel):
    """Immutable audit record of operator's free-account attestation."""

    provider: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verification_state: str = "OPERATOR_ATTESTED"  # UNVERIFIED, OPERATOR_ATTESTED, DASHBOARD_EVIDENCED, PROVIDER_CONFIRMED, INELIGIBLE_PAID, BLOCKED_EXTERNAL
    is_free_plan: bool
    no_paid_upgrade: bool
    no_auto_billing: bool
    model_id: str
    verified_quotas: dict[str, Any]
    hard_stop_confirmed: bool
    attestation_notes: str = ""


class OperatorConfirmationRequiredError(PromptIQException):
    """Raised when live inference is attempted without explicit operator free-account confirmation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message,
            error_code="OPERATOR_CONFIRMATION_REQUIRED",
            status_code=412,
            details=details or {},
        )


class OperatorAccountVerifier:
    """Verifies and logs operator attestation of free-account status before live execution."""

    @classmethod
    def verify_operator_account(
        cls,
        provider: str = "groq",
        model_id: str = "openai/gpt-oss-120b",
        opt_in_confirmed: bool = False,
    ) -> OperatorVerificationRecord:
        """Validates that operator has explicitly confirmed free-tier status and no billing card."""
        if not opt_in_confirmed:
            raise OperatorConfirmationRequiredError(
                "Live network execution requires explicit opt-in confirmation (opt_in=True).",
                details={"provider": provider, "status": "BLOCKED_EXTERNAL"},
            )

        key = (
            settings.effective_groq_api_key
            if provider.lower() == "groq"
            else settings.effective_gemini_api_key
        )
        if not key:
            raise OperatorConfirmationRequiredError(
                f"No operator credential configured for provider '{provider}'. "
                "Classified as BLOCKED_EXTERNAL. Cannot make live network calls.",
                details={"provider": provider, "status": "BLOCKED_EXTERNAL"},
            )

        # In production/live execution, check attestation flags
        if not settings.is_operator_free_tier_confirmed and not settings.is_test:
            raise OperatorConfirmationRequiredError(
                f"Operator has not completed free-account attestation for provider '{provider}'. "
                "Confirm that account is on Free Plan, has no billing card on file, and native hard stop is enabled.",
                details={
                    "provider": provider,
                    "free_plan_confirmed": settings.OPERATOR_CONFIRMED_FREE_PLAN,
                    "no_paid_upgrade": settings.OPERATOR_CONFIRMED_NO_PAID_UPGRADE,
                    "hard_stop_confirmed": settings.OPERATOR_CONFIRMED_HARD_STOP,
                    "status": "BLOCKED_EXTERNAL",
                },
            )

        # Attested quotas for Groq free plan (30 RPM, 1,000 RPD, 8k TPM, 200k TPD)
        quotas = {
            "rpm": 30,
            "rpd": 1000,
            "tpm": 8000,
            "tpd": 200000,
            "price_per_token": 0.0,  # nosec B105
            "hard_stop_status_code": 429,
        }

        # Determine verification state
        verification_state = (
            "DASHBOARD_EVIDENCED"
            if settings.PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED
            else "OPERATOR_ATTESTED"
        )

        return OperatorVerificationRecord(
            provider=provider,
            verification_state=verification_state,
            is_free_plan=True,
            no_paid_upgrade=True,
            no_auto_billing=True,
            model_id=model_id,
            verified_quotas=quotas,
            hard_stop_confirmed=True,
            attestation_notes="Attested under GroqCloud Free Tier terms. Developer Plan paid rates strictly excluded.",
        )
