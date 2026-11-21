"""Tests for Model Registry, Model-Specific Rate Limits, Cost Eligibility Gate, and Live Tournament Disclosures."""

import pytest

from promptiq.core.cost_gate import CostEligibilityGate, InfrastructureCostViolationError
from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.eval.tournament import ModelTournamentRunner
from promptiq.gateway.governor import CapacityGovernor
from promptiq.registry.model_registry import ModelRegistryService


def test_model_registry_eligibility_and_retirements():
    """Verifies that retired models are flagged and dated, and active models have verified free quotas."""
    all_models = ModelRegistryService.list_models()
    model_map = {m.model_id: m for m in all_models}

    # Gemini 2.0 Flash is shutdown and NOT marked as active zero-price route
    gemini_2 = model_map["gemini-2.0-flash"]
    assert gemini_2.is_zero_price is False
    assert gemini_2.eligibility_status == "retired_shutdown"
    assert "2026-06-01" in (gemini_2.retirement_date or "")

    # Gemini 3.8 Flash is active zero-price
    gemini_38 = model_map["gemini-3.8-flash"]
    assert gemini_38.is_zero_price is True
    assert gemini_38.eligibility_status == "eligible_zero_price"
    assert gemini_38.rate_limits["rpd"] == 1500

    # Groq Llama 3.3 70B has exact 1,000 RPD and 100,000 TPD limits (NOT generic 14,400)
    llama_70b = model_map["llama-3.3-70b-versatile"]
    assert llama_70b.rate_limits["rpd"] == 1000
    assert llama_70b.rate_limits["tpd"] == 100000

    # Groq Llama 3.1 8B has 14,400 RPD
    llama_8b = model_map["llama-3.1-8b-instant"]
    assert llama_8b.rate_limits["rpd"] == 14400
    assert llama_8b.rate_limits["tpd"] == 500000


def test_capacity_governor_model_specific_quotas():
    """Verifies that model-specific RPM/RPD/TPM/TPD rate limits are strictly enforced."""
    gov = CapacityGovernor()

    # Simulate 30 requests for llama-3.3-70b-versatile (reaches RPM limit)
    for _ in range(30):
        gov.record_model_usage("llama-3.3-70b-versatile", tokens_used=100)

    # 31st request MUST raise CapacityExhaustedError
    with pytest.raises(CapacityExhaustedError) as exc_info:
        gov.check_model_quota("llama-3.3-70b-versatile")
    assert "rpm" in exc_info.value.message.lower() or "rate limit" in exc_info.value.message.lower()


def test_capacity_governor_header_inspection():
    """Verifies that response headers from providers trigger accurate circuit breaker pauses."""
    gov = CapacityGovernor()

    # Provider returns HTTP 429 with Retry-After: 45
    gov.inspect_response_headers("groq", "llama-3.3-70b-versatile", {"retry-after": "45"}, status_code=429)

    # Circuit breaker must be active
    with pytest.raises(CapacityExhaustedError) as exc_info:
        gov.check_circuit_breaker("groq")
    assert exc_info.value.retry_after >= 40


def test_cost_eligibility_gate():
    """Verifies the CostEligibilityGate enforces zero-spend infrastructure invariant."""
    # Neon serverless postgres is approved (true hard stop, no billing card required)
    neon_audit = CostEligibilityGate.audit_resource("neon_postgres")
    assert neon_audit["is_zero_spend_guaranteed"] is True
    CostEligibilityGate.verify_resource_provisioning("neon_postgres")

    # Cloudflare workers is approved
    CostEligibilityGate.verify_resource_provisioning("cloudflare_workers")

    # Google Cloud Run requires credit card and auto-charges overage; MUST be rejected for auto-provisioning
    with pytest.raises(InfrastructureCostViolationError) as exc_info:
        CostEligibilityGate.verify_resource_provisioning("google_cloud_run")
    assert "billing account" in exc_info.value.message.lower() or "hard stop" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_tournament_live_disclosure_unverified():
    """Verifies that without operator credentials, tournament marks live provider UNVERIFIED without fake scores."""
    runner = ModelTournamentRunner()

    # 1. Retired model returns RETIRED_AND_INELIGIBLE
    res_retired = await runner.evaluate_live_provider("gemini", "gemini-2.0-flash")
    assert res_retired["status"] == "RETIRED_AND_INELIGIBLE"
    assert res_retired["sample_size"] == 0

    # 2. Live model without operator key returns UNVERIFIED
    res_unverified = await runner.evaluate_live_provider("gemini", "gemini-3.8-flash", operator_api_key=None)
    assert "UNVERIFIED" in res_unverified["status"]
    assert res_unverified["sample_size"] == 0
    assert "Never manufacture scores" in res_unverified["notice"]
