"""Tests for Operator Smoke-Test Utility and Account Verification."""

import pytest

from promptiq.core.exceptions import ZeroPriceViolationError
from promptiq.gateway.account_verification import (
    OperatorAccountVerifier,
    OperatorConfirmationRequiredError,
)
from promptiq.gateway.smoke_test import execute_live_smoke_test


def test_operator_account_verifier_requires_opt_in():
    """Verifies that OperatorAccountVerifier blocks execution when opt_in is False."""
    with pytest.raises(OperatorConfirmationRequiredError) as exc_info:
        OperatorAccountVerifier.verify_operator_account(provider="groq", opt_in_confirmed=False)
    assert exc_info.value.details["status"] == "BLOCKED_EXTERNAL"
    assert "opt-in confirmation" in exc_info.value.message


@pytest.mark.asyncio
async def test_smoke_test_without_opt_in_returns_blocked_external():
    """Verifies execute_live_smoke_test returns BLOCKED_EXTERNAL without opt-in."""
    result = await execute_live_smoke_test(
        provider="groq",
        model_id="openai/gpt-oss-120b",
        opt_in=False,
    )
    assert result["status"] == "BLOCKED_EXTERNAL"
    assert result["success"] is False
    assert result["http_status"] is None
    assert "opt-in confirmation" in result["error"]
    assert "Never substitute mock execution" in result["notice"]


@pytest.mark.asyncio
async def test_smoke_test_with_opt_in_missing_credentials_returns_blocked_external():
    """Verifies execute_live_smoke_test returns BLOCKED_EXTERNAL when credentials are absent."""
    result = await execute_live_smoke_test(
        provider="groq",
        model_id="openai/gpt-oss-120b",
        opt_in=True,
    )
    assert result["status"] == "BLOCKED_EXTERNAL"
    assert result["success"] is False
    assert result["http_status"] is None
    assert "No operator credential configured" in result["error"]


@pytest.mark.asyncio
async def test_smoke_test_rejects_retired_model():
    """Verifies execute_live_smoke_test rejects retired models via ZeroPriceViolationError."""
    with pytest.raises(ZeroPriceViolationError):
        await execute_live_smoke_test(
            provider="groq",
            model_id="llama-3.3-70b-versatile",
            opt_in=True,
        )
