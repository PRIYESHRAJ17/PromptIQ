"""Test Zero-Price Model Gateway, BYOK Prohibitor, and Capacity Governor."""

import pytest

from promptiq.core.exceptions import (
    BYOKViolationError,
    CapacityExhaustedError,
    ZeroPriceViolationError,
)
from promptiq.gateway.eligibility import check_and_reject_byok, verify_zero_price_route
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.governor import governor
from promptiq.gateway.models import GatewayMessage, InferenceRequest


@pytest.mark.asyncio
async def test_zero_price_eligibility_gate():
    """
    REQ-CORE-002 Invariant:
    Verify that any attempt to use a paid route or non-zero price is rejected immediately.
    """
    # Allowed $0 routes pass
    verify_zero_price_route(provider="mock", model_id="promptiq-mock-v1", price_per_token=0.0)
    verify_zero_price_route(provider="gemini", model_id="gemini-2.0-flash", price_per_token=0.0)
    verify_zero_price_route(provider="groq", model_id="llama-3.3-70b-versatile", price_per_token=0.0)

    # Paid routes MUST raise ZeroPriceViolationError
    with pytest.raises(ZeroPriceViolationError):
        verify_zero_price_route(provider="openai", model_id="gpt-4o", price_per_token=0.005)

    with pytest.raises(ZeroPriceViolationError):
        verify_zero_price_route(provider="anthropic", model_id="claude-3-7-sonnet", price_per_token=0.003)

    # Unverified route without :free tag raises error
    with pytest.raises(ZeroPriceViolationError):
        verify_zero_price_route(provider="unverified_vendor", model_id="commercial-model-v1", price_per_token=0.0)


@pytest.mark.asyncio
async def test_prohibited_byok_rejection():
    """
    REQ-CORE-002 Invariant:
    Verify that no user-supplied API keys (BYOK) are ever accepted.
    """
    # Clean payload passes
    check_and_reject_byok({"prompt": "Hello", "task": "coding"})

    # Payloads containing user keys MUST raise BYOKViolationError
    with pytest.raises(BYOKViolationError):
        check_and_reject_byok({"prompt": "test", "openai_api_key": "sk-1234567890"})

    with pytest.raises(BYOKViolationError):
        check_and_reject_byok({"anthropic_api_key": "sk-ant-1234567890"})

    with pytest.raises(BYOKViolationError):
        check_and_reject_byok({"settings": {"user_api_key": "custom_key_123"}})


@pytest.mark.asyncio
async def test_deterministic_mock_inference():
    """Verifies that the default mock adapter executes offline with route_cost == 0.0."""
    req = InferenceRequest(
        messages=[GatewayMessage(role="user", content="Test prompt compilation")],
        task_context="general",
        user_id="test_user",
    )
    resp = await inference_gateway.generate(req, provider="mock")

    assert resp.model_id == "promptiq-mock-v1"
    assert resp.provider == "mock"
    assert resp.route_cost == 0.0  # Hard invariant
    assert len(resp.text) > 0


@pytest.mark.asyncio
async def test_capacity_governor_circuit_breaker():
    """Verifies that the circuit breaker pauses requests on upstream errors."""
    provider = "test_failing_route"
    governor.trip_circuit_breaker(provider, reason="Simulated 429 rate limit", pause_duration_seconds=5)

    # Subsequent check must raise CapacityExhaustedError
    with pytest.raises(CapacityExhaustedError) as exc_info:
        governor.check_circuit_breaker(provider)

    assert "paused" in exc_info.value.message.lower()
    assert exc_info.value.retry_after > 0
