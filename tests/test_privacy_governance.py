"""Test Privacy-Aware Routing and Provider Data Governance."""

import pytest

from promptiq.core.exceptions import PrivacyPolicyViolationError
from promptiq.gateway.model_pool import ModelPoolService
from promptiq.gateway.privacy_governance import PrivacyGovernanceService
from promptiq.schemas.model_pool import DataSensitivityLevel


def test_public_and_general_data_allowed_on_standard_providers():
    """Verifies that PUBLIC and GENERAL data can route to verified zero-price providers."""
    # Should not raise
    PrivacyGovernanceService.validate_task_privacy(
        DataSensitivityLevel.PUBLIC, "google", "gemini-3.8-flash"
    )
    PrivacyGovernanceService.validate_task_privacy(
        DataSensitivityLevel.GENERAL, "groq", "openai/gpt-oss-120b"
    )


def test_confidential_data_rejects_google_free_tier():
    """Verifies that CONFIDENTIAL data is strictly blocked from Google free tier due to human review terms."""
    with pytest.raises(PrivacyPolicyViolationError) as exc_info:
        PrivacyGovernanceService.validate_task_privacy(
            DataSensitivityLevel.CONFIDENTIAL, "google", "gemini-3.8-flash"
        )
    assert "human review or model training" in str(exc_info.value)


def test_restricted_data_rejects_all_external_free_providers():
    """Verifies that RESTRICTED compliance data is blocked from all external cloud APIs."""
    for provider, model in [
        ("google", "gemini-3.8-flash"),
        ("groq", "openai/gpt-oss-120b"),
        ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"),
    ]:
        with pytest.raises(PrivacyPolicyViolationError) as exc_info:
            PrivacyGovernanceService.validate_task_privacy(
                DataSensitivityLevel.RESTRICTED, provider, model
            )
        assert "RESTRICTED data requires zero-egress internal execution" in str(exc_info.value)

    assert (
        PrivacyGovernanceService.is_generative_ai_permitted(DataSensitivityLevel.RESTRICTED)
        is False
    )
    assert (
        PrivacyGovernanceService.is_generative_ai_permitted(DataSensitivityLevel.CONFIDENTIAL)
        is True
    )
    assert PrivacyGovernanceService.is_generative_ai_permitted(DataSensitivityLevel.GENERAL) is True


def test_filter_models_for_sensitivity():
    """Tests candidate model filtering based on data sensitivity tier."""
    all_models = ModelPoolService.get_verified_eligible_models(include_conditional=True)

    general_models = PrivacyGovernanceService.filter_models_for_sensitivity(
        all_models, DataSensitivityLevel.GENERAL
    )
    assert any(m.provider == "google" for m in general_models)
    assert any(m.provider == "groq" for m in general_models)

    confidential_models = PrivacyGovernanceService.filter_models_for_sensitivity(
        all_models, DataSensitivityLevel.CONFIDENTIAL
    )
    # Google free tier must be excluded from CONFIDENTIAL
    assert not any(m.provider == "google" for m in confidential_models)
    assert any(m.provider == "groq" for m in confidential_models)

    restricted_models = PrivacyGovernanceService.filter_models_for_sensitivity(
        all_models, DataSensitivityLevel.RESTRICTED
    )
    # Only internal/mock permitted for RESTRICTED
    assert len(restricted_models) >= 1
    assert all(m.provider == "mock" for m in restricted_models)


def test_audience_terms_rejection_for_minors():
    """Verifies that Google Gemini API terms reject applications targeting minors (<18)."""
    with pytest.raises(PrivacyPolicyViolationError) as exc_info:
        PrivacyGovernanceService.validate_audience_terms(
            "google", "gemini-3.8-flash", target_audience_includes_minors=True
        )
    assert "under 18" in str(exc_info.value)

    # Groq and mock allow minor audience without raising
    PrivacyGovernanceService.validate_audience_terms(
        "groq", "openai/gpt-oss-120b", target_audience_includes_minors=True
    )
    PrivacyGovernanceService.validate_audience_terms(
        "mock", "promptiq-mock-v1", target_audience_includes_minors=True
    )
