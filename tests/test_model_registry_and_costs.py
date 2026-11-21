"""Tests for Model Registry, Model-Specific Rate Limits, Cost Eligibility Gate, and Live Tournament Disclosures."""

import pytest

from promptiq.core.cost_gate import CostEligibilityGate, InfrastructureCostViolationError
from promptiq.core.exceptions import CapacityExhaustedError, ZeroPriceViolationError
from promptiq.eval.tournament import ModelTournamentRunner
from promptiq.gateway.eligibility import RETIRED_MODELS, verify_zero_price_route
from promptiq.gateway.governor import CapacityGovernor
from promptiq.gateway.model_pool import ModelPoolService
from promptiq.orchestrator.router import DynamicModelRouter
from promptiq.registry.model_registry import ModelRegistryService
from promptiq.schemas.model_pool import DataSensitivityLevel, EligibilityState, LogicalModelRole


def test_model_registry_eligibility_and_retirements():
    """Verifies that retired models are flagged and dated, and active models have verified free quotas."""
    all_models = ModelRegistryService.list_models()
    model_map = {m.model_id: m for m in all_models}

    # Gemini 2.0 Flash is shutdown and NOT marked as active zero-price route
    gemini_2 = model_map["gemini-2.0-flash"]
    assert gemini_2.is_zero_price is False
    assert gemini_2.eligibility_status == "retired_shutdown"
    assert "2026-06-01" in (gemini_2.retirement_date or "")

    # Groq retired models are shutdown and NOT marked as active zero-price route
    for ret_id in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-2.5-coder-32b"]:
        m = model_map[ret_id]
        assert m.is_zero_price is False
        assert m.eligibility_status == "retired_shutdown"
        assert "2026-10-31" in (m.retirement_date or "")

    # Gemini 3.8 Flash is active zero-price
    gemini_38 = model_map["gemini-3.8-flash"]
    assert gemini_38.is_zero_price is True
    assert gemini_38.eligibility_status == "eligible_zero_price"
    assert gemini_38.rate_limits["rpd"] == 1500

    # Groq OpenAI GPT-OSS 120B has exact 1,000 RPD and 100,000 TPD limits
    gpt_120b = model_map["openai/gpt-oss-120b"]
    assert gpt_120b.is_zero_price is True
    assert gpt_120b.rate_limits["rpd"] == 1000
    assert gpt_120b.rate_limits["tpd"] == 100000

    # Groq OpenAI GPT-OSS 20B has 14,400 RPD
    gpt_20b = model_map["openai/gpt-oss-20b"]
    assert gpt_20b.is_zero_price is True
    assert gpt_20b.rate_limits["rpd"] == 14400
    assert gpt_20b.rate_limits["tpd"] == 500000


def test_retired_groq_and_gemini_models_strictly_rejected():
    """Regression test: retired models must be refused by route verification and never entered into active pool."""
    for retired_id in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-2.5-coder-32b", "gemini-2.0-flash"]:
        assert retired_id in RETIRED_MODELS
        # Route check must strictly fail
        with pytest.raises(ZeroPriceViolationError) as exc_info:
            verify_zero_price_route(provider="groq" if "llama" in retired_id or "qwen" in retired_id else "gemini", model_id=retired_id)
        assert "retired" in exc_info.value.message.lower()

        # Model pool record must be RETIRED
        pool_record = ModelPoolService.get_model(retired_id)
        assert pool_record is not None
        assert pool_record.eligibility_state == EligibilityState.RETIRED
        assert pool_record.is_zero_price is False

    # Router must never select any retired model for any role
    for role in [LogicalModelRole.FAST, LogicalModelRole.REASONING, LogicalModelRole.CRITIC]:
        selected = DynamicModelRouter.select_model_for_role(role=role, sensitivity=DataSensitivityLevel.GENERAL)
        assert selected.model_id not in RETIRED_MODELS
        assert selected.eligibility_state == EligibilityState.VERIFIED_ELIGIBLE


def test_capacity_governor_model_specific_quotas():
    """Verifies that model-specific RPM/RPD/TPM/TPD rate limits are strictly enforced."""
    gov = CapacityGovernor()

    # Simulate 30 requests for openai/gpt-oss-120b (reaches RPM limit)
    for _ in range(30):
        gov.record_model_usage("openai/gpt-oss-120b", tokens_used=100)

    # 31st request MUST raise CapacityExhaustedError
    with pytest.raises(CapacityExhaustedError) as exc_info:
        gov.check_model_quota("openai/gpt-oss-120b")
    assert "rpm" in exc_info.value.message.lower() or "rate limit" in exc_info.value.message.lower()


def test_capacity_governor_header_inspection():
    """Verifies that response headers from providers trigger accurate circuit breaker pauses."""
    gov = CapacityGovernor()

    # Provider returns HTTP 429 with Retry-After: 45
    gov.inspect_response_headers("groq", "openai/gpt-oss-120b", {"retry-after": "45"}, status_code=429)

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

    # Cloudflare workers is approved for edge proxy
    CostEligibilityGate.verify_resource_provisioning("cloudflare_workers")

    # Render web service is NOT approved for production backend
    with pytest.raises(InfrastructureCostViolationError) as exc_info:
        CostEligibilityGate.verify_resource_provisioning("render_web_service")
    assert "rejected" in exc_info.value.message.lower()

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


def test_candidate_ineligibility_and_conditions():
    """Verifies that candidates evaluated during Phase 3.3 have accurate non-eligible / conditional states."""
    cerebras = ModelPoolService.get_model("cerebras/llama-3.3-70b")
    assert cerebras is not None
    assert cerebras.eligibility_state == EligibilityState.INELIGIBLE_BILLING

    sambanova = ModelPoolService.get_model("sambanova/Meta-Llama-3.3-70B-Instruct")
    assert sambanova is not None
    assert sambanova.eligibility_state == EligibilityState.INELIGIBLE_TERMS

    nvidia = ModelPoolService.get_model("nvidia/meta/llama-3.3-70b-instruct")
    assert nvidia is not None
    assert nvidia.eligibility_state == EligibilityState.INELIGIBLE_TERMS

    cf_llama = ModelPoolService.get_model("@cf/meta/llama-3.1-8b-instruct")
    assert cf_llama is not None
    assert cf_llama.eligibility_state == EligibilityState.CONDITIONALLY_ELIGIBLE

