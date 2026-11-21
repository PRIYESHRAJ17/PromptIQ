"""Dynamic Model Router for multi-model intelligence and capability-aware routing."""

from typing import Any

from promptiq.core.exceptions import CapacityExhaustedError, ZeroPriceViolationError
from promptiq.gateway.eligibility import RETIRED_MODELS, verify_zero_price_route
from promptiq.gateway.governor import capacity_governor
from promptiq.gateway.model_pool import ModelPoolService
from promptiq.gateway.privacy_governance import PrivacyGovernanceService
from promptiq.schemas.model_pool import (
    DataSensitivityLevel,
    EligibilityState,
    LogicalModelRole,
    ModelPoolRecord,
)


class DynamicModelRouter:
    """Dynamically routes tasks to eligible zero-price models based on role, privacy, and capacity."""

    @classmethod
    def verify_candidate_eligibility(
        cls,
        candidate: ModelPoolRecord,
        sensitivity: DataSensitivityLevel = DataSensitivityLevel.GENERAL,
    ) -> None:
        """Independently verifies that a candidate strictly satisfies zero-price and eligibility rules."""
        # 1. Reject retired models
        if candidate.model_id.lower() in RETIRED_MODELS or candidate.id.lower() in RETIRED_MODELS:
            reason = RETIRED_MODELS.get(candidate.model_id.lower(), "Retired model")
            raise ZeroPriceViolationError(
                provider=candidate.provider,
                model_id=candidate.model_id,
                reason=f"Candidate model '{candidate.model_id}' is permanently retired ({reason}) and cannot be routed.",
            )

        # 2. Strict eligibility state check
        if candidate.eligibility_state != EligibilityState.VERIFIED_ELIGIBLE:
            raise ZeroPriceViolationError(
                provider=candidate.provider,
                model_id=candidate.model_id,
                reason=f"Candidate model '{candidate.model_id}' has state '{candidate.eligibility_state.value}'. Only VERIFIED_ELIGIBLE models can be routed.",
            )

        # 3. Hard zero-price enforcement
        if not candidate.is_zero_price or candidate.cost_input_per_token > 0.0 or candidate.cost_output_per_token > 0.0:
            raise ZeroPriceViolationError(
                provider=candidate.provider,
                model_id=candidate.model_id,
                reason=f"Candidate model '{candidate.model_id}' has non-zero pricing and is prohibited.",
            )

        # 4. Route registry check
        verify_zero_price_route(candidate.provider, candidate.model_id, price_per_token=0.0)

        # 5. Data sensitivity and privacy policy check
        PrivacyGovernanceService.validate_task_privacy(sensitivity, candidate.provider, candidate.model_id)

    @classmethod
    def select_model_for_role(
        cls,
        role: LogicalModelRole,
        sensitivity: DataSensitivityLevel = DataSensitivityLevel.GENERAL,
        required_context: int = 4000,
        exclude_families: list[str] | None = None,
        estimated_tokens: int = 1000,
    ) -> ModelPoolRecord:
        """Selects the best available verified zero-price model for a given role and constraints."""
        candidates = ModelPoolService.get_candidates_for_role(
            role=role,
            sensitivity=sensitivity,
            required_context_length=required_context,
        )

        excluded = set(exclude_families or [])

        # Filter out excluded families (used for independent critic separation)
        eligible_candidates = [c for c in candidates if c.model_family not in excluded]

        if not eligible_candidates:
            # If all candidates were excluded due to family constraint, check if we have any other candidates
            # but preserve critic independence principle
            if excluded:
                raise CapacityExhaustedError(
                    message=f"No independent model family available for role '{role.value}' distinct from {list(excluded)}.",
                    retry_after=30,
                    details={"role": role.value, "excluded_families": list(excluded)},
                )
            raise CapacityExhaustedError(
                message=f"No verified zero-price models available for role '{role.value}' with sensitivity '{sensitivity.value}'.",
                retry_after=60,
                details={"role": role.value, "sensitivity": sensitivity.value},
            )

        # Check circuit breaker and capacity for each candidate
        last_error_details: dict[str, Any] = {}
        for candidate in eligible_candidates:
            # Independent eligibility gate check
            try:
                cls.verify_candidate_eligibility(candidate, sensitivity=sensitivity)
            except (ZeroPriceViolationError, Exception) as e:
                last_error_details[candidate.model_id] = f"Eligibility violation: {e}"
                continue

            # 1. Circuit breaker check
            try:
                capacity_governor.check_circuit_breaker(candidate.provider)
            except CapacityExhaustedError as e:
                last_error_details[candidate.model_id] = f"Circuit breaker tripped on {candidate.provider}: {e.message}"
                continue

            # 2. Model-specific quota check
            try:
                capacity_governor.check_model_quota(candidate.model_id, estimated_tokens=estimated_tokens)
            except CapacityExhaustedError as e:
                last_error_details[candidate.model_id] = f"Quota limit reached: {e.message}"
                continue

            # Route is verified eligible and has capacity
            return candidate

        # If all candidates exhausted their capacity
        raise CapacityExhaustedError(
            message=f"All eligible zero-price routes for role '{role.value}' have reached quota limits or failed verification. Work paused to prevent paid billing.",
            retry_after=60,
            details={"role": role.value, "candidate_exhaustions": last_error_details},
        )
