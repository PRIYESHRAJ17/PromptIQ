"""Provider Data Governance and Privacy-Aware Routing."""

from promptiq.core.exceptions import PrivacyPolicyViolationError
from promptiq.schemas.model_pool import DataSensitivityLevel, ModelPoolRecord, ProviderPrivacyCard

# Canonical provider privacy profiles with dated terms (late 2026)
PROVIDER_PRIVACY_PROFILES: dict[str, ProviderPrivacyCard] = {
    "google": ProviderPrivacyCard(
        training_policy="human_review_for_training",
        data_retention_days=30,
        deletion_api_available=False,
        jurisdiction="United States",
        allows_confidential_data=False,
        privacy_notes="Google AI Studio free tier logs prompts and outputs for human review and model improvement. Rejects CONFIDENTIAL/RESTRICTED.",
    ),
    "groq": ProviderPrivacyCard(
        training_policy="no_training_opt_out_default",
        data_retention_days=30,
        deletion_api_available=False,
        jurisdiction="United States",
        allows_confidential_data=True,
        privacy_notes="GroqCloud free tier does not train base models on user prompts. Retention 30 days for abuse detection. Allows CONFIDENTIAL.",
    ),
    "openrouter": ProviderPrivacyCard(
        training_policy="variable_upstream_terms",
        data_retention_days=30,
        deletion_api_available=False,
        jurisdiction="United States",
        allows_confidential_data=False,
        privacy_notes="OpenRouter free tier routes to variable upstream hosts. Logs may be retained by intermediary. Rejects CONFIDENTIAL/RESTRICTED.",
    ),
    "mock": ProviderPrivacyCard(
        training_policy="zero_retention_internal",
        data_retention_days=0,
        deletion_api_available=True,
        jurisdiction="Local/Internal",
        allows_confidential_data=True,
        privacy_notes="Deterministic internal mock generator. Zero external egress, zero retention. Safe for all classifications including RESTRICTED.",
    ),
}

# Hierarchy of sensitivity levels: PUBLIC (0) < GENERAL (1) < CONFIDENTIAL (2) < RESTRICTED (3)
SENSITIVITY_HIERARCHY: dict[DataSensitivityLevel, int] = {
    DataSensitivityLevel.PUBLIC: 0,
    DataSensitivityLevel.GENERAL: 1,
    DataSensitivityLevel.CONFIDENTIAL: 2,
    DataSensitivityLevel.RESTRICTED: 3,
}


class PrivacyGovernanceService:
    """Evaluates task data sensitivity and enforces zero-leakage routing rules."""

    @staticmethod
    def get_provider_privacy_card(provider: str) -> ProviderPrivacyCard:
        prov = provider.lower()
        if prov in PROVIDER_PRIVACY_PROFILES:
            return PROVIDER_PRIVACY_PROFILES[prov]
        # Default restrictive card for unrecognized providers
        return ProviderPrivacyCard(
            training_policy="unverified_terms",
            data_retention_days=90,
            deletion_api_available=False,
            jurisdiction="Unknown",
            allows_confidential_data=False,
            privacy_notes="Unverified external provider. Conservative privacy classification applied.",
        )

    @classmethod
    def validate_task_privacy(
        cls,
        task_sensitivity: DataSensitivityLevel,
        provider: str,
        model_id: str,
    ) -> None:
        """Validates that a task's sensitivity does not violate the provider's data terms.

        Raises PrivacyPolicyViolationError if routing would violate terms.
        """
        privacy_card = cls.get_provider_privacy_card(provider)

        # RESTRICTED data can ONLY be processed by internal zero-retention routes
        if task_sensitivity == DataSensitivityLevel.RESTRICTED:
            if provider.lower() not in ("mock", "internal"):
                raise PrivacyPolicyViolationError(
                    provider=provider,
                    model_id=model_id,
                    sensitivity=task_sensitivity.value,
                    reason="RESTRICTED data requires zero-egress internal execution; external free APIs are forbidden.",
                )
            return

        # CONFIDENTIAL data cannot be routed to providers that use data for training or human review
        if task_sensitivity == DataSensitivityLevel.CONFIDENTIAL:
            if not privacy_card.allows_confidential_data or privacy_card.training_policy == "human_review_for_training":
                raise PrivacyPolicyViolationError(
                    provider=provider,
                    model_id=model_id,
                    sensitivity=task_sensitivity.value,
                    reason=f"Provider '{provider}' terms ({privacy_card.training_policy}) allow human review or model training on free-tier requests.",
                )

    @classmethod
    def filter_models_for_sensitivity(
        cls,
        models: list[ModelPoolRecord],
        task_sensitivity: DataSensitivityLevel,
    ) -> list[ModelPoolRecord]:
        """Filters a candidate list of models, keeping only those safe for the task sensitivity."""
        task_rank = SENSITIVITY_HIERARCHY[task_sensitivity]
        eligible: list[ModelPoolRecord] = []

        for m in models:
            max_allowed = m.max_allowed_data_sensitivity
            max_rank = SENSITIVITY_HIERARCHY.get(max_allowed, 1)

            if task_rank <= max_rank:
                # Additional check on provider privacy card
                if task_sensitivity in (DataSensitivityLevel.CONFIDENTIAL, DataSensitivityLevel.RESTRICTED):
                    try:
                        cls.validate_task_privacy(task_sensitivity, m.provider, m.model_id)
                        eligible.append(m)
                    except PrivacyPolicyViolationError:
                        continue
                else:
                    eligible.append(m)

        return eligible
