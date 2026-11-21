"""Test Multi-Model Pool Architecture and Role Candidate Resolution."""

from promptiq.gateway.model_pool import ModelPoolService
from promptiq.schemas.model_pool import (
    EligibilityState,
    LogicalModelRole,
)


def test_model_pool_contents_and_eligibility():
    """Verifies that all models in the pool have explicit eligibility states and $0 costs."""
    models = ModelPoolService.list_models(zero_price_only=False)
    assert len(models) >= 9

    # Strict verified eligible production models (Groq GPT-OSS 120B, 20B, internal mock)
    verified = ModelPoolService.get_verified_eligible_models(include_conditional=False)
    assert len(verified) >= 3

    for m in verified:
        assert m.eligibility_state == EligibilityState.VERIFIED_ELIGIBLE
        assert m.is_zero_price is True
        assert m.cost_input_per_token == 0.0
        assert m.cost_output_per_token == 0.0
        assert m.verification_date is not None
        assert m.source_url.startswith(("http", "internal"))

    # Conditional models (Gemini adult-only, Cloudflare Workers AI, OpenRouter free)
    conditional = ModelPoolService.list_models(eligibility_state=EligibilityState.CONDITIONALLY_ELIGIBLE)
    assert len(conditional) >= 4

    # Preview models (Qwen 3.8 27B isolated to evaluation)
    preview = ModelPoolService.list_models(eligibility_state=EligibilityState.REVIEW_REQUIRED)
    assert len(preview) >= 1
    assert any(m.model_id == "qwen/qwen3.8-27b" for m in preview)


def test_retired_and_paid_models_flagged():
    """Verifies that retired and paid models have non-eligible states."""
    gemini_2_flash = ModelPoolService.get_model("gemini-2.0-flash")
    assert gemini_2_flash is not None
    assert gemini_2_flash.eligibility_state == EligibilityState.RETIRED
    assert gemini_2_flash.is_zero_price is False

    for groq_ret in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-2.5-coder-32b"]:
        m = ModelPoolService.get_model(groq_ret)
        assert m is not None
        assert m.eligibility_state == EligibilityState.RETIRED
        assert m.is_zero_price is False

    claude_paid = ModelPoolService.get_model("claude-3-7-sonnet")
    assert claude_paid is not None
    assert claude_paid.eligibility_state == EligibilityState.INELIGIBLE_PAID
    assert claude_paid.is_zero_price is False


def test_candidates_for_role_matching():
    """Tests logical role candidate retrieval with capabilities and context window checks."""
    # Orchestrator candidates
    orch_candidates = ModelPoolService.get_candidates_for_role(LogicalModelRole.ORCHESTRATOR)
    assert len(orch_candidates) >= 1
    for c in orch_candidates:
        assert c.capabilities.tools is True

    # Critic candidates
    critic_candidates = ModelPoolService.get_candidates_for_role(LogicalModelRole.CRITIC)
    assert len(critic_candidates) >= 1
    for c in critic_candidates:
        assert c.capabilities.reasoning is True
        assert c.composite_score >= 0.85
