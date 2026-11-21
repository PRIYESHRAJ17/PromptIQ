"""Zero-Price Eligibility Gate and BYOK Prohibitor."""

from typing import Any

from promptiq.core.exceptions import BYOKViolationError, ZeroPriceViolationError

# Known verified zero-price provider routes
VERIFIED_ZERO_PRICE_ROUTES = {
    "mock": ["promptiq-mock-v1", "deterministic-mock-v1"],
    "gemini": ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "openrouter": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "deepseek/deepseek-r1:free",
    ],
}

PROHIBITED_KEY_FIELDS = {
    "api_key",
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
    "groq_api_key",
    "user_api_key",
    "byok_key",
    "search_api_key",
}


def verify_zero_price_route(provider: str, model_id: str, price_per_token: float = 0.0) -> None:
    """Enforces the non-negotiable zero-price invariant. Rejects any route with non-zero pricing."""
    if price_per_token > 0.0:
        raise ZeroPriceViolationError(
            provider=provider,
            model_id=model_id,
            reason=f"Route has non-zero pricing (${price_per_token}/token). Only $0 routes are permitted.",
        )

    provider_routes = VERIFIED_ZERO_PRICE_ROUTES.get(provider.lower())
    if not provider_routes or model_id not in provider_routes:
        # Check if model has explicit :free tag
        if not model_id.endswith(":free"):
            raise ZeroPriceViolationError(
                provider=provider,
                model_id=model_id,
                reason="Model is not an officially verified zero-price route.",
            )


def check_and_reject_byok(data: dict[str, Any] | None) -> None:
    """Detects and strictly rejects any user-supplied API key payload."""
    if not data or not isinstance(data, dict):
        return

    for key in data.keys():
        if key.lower() in PROHIBITED_KEY_FIELDS:
            raise BYOKViolationError(
                f"Prohibited field '{key}' detected. PromptIQ is 100% free; user API keys are strictly forbidden."
            )
        # Check nested dictionaries
        if isinstance(data[key], dict):
            check_and_reject_byok(data[key])
