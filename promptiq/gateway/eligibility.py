"""Zero-Price Eligibility Gate and BYOK Prohibitor."""

from typing import Any

from promptiq.core.exceptions import BYOKViolationError, ZeroPriceViolationError

# Known verified zero-price provider routes and active model versions (as of late 2026)
VERIFIED_ZERO_PRICE_ROUTES: dict[str, list[str]] = {
    "mock": ["promptiq-mock-v1", "deterministic-mock-v1"],
    "gemini": [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
    ],
    "groq": [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
    ],
    "openrouter": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free",
        "baidu/ernie-5.5-flash-preview:free",
    ],
}

# Officially retired / shut-down models that are strictly rejected by the gateway
RETIRED_MODELS: dict[str, str] = {
    "gemini-2.0-flash": "Shut down on June 1, 2026",
    "gemini-2.0-flash-lite": "Shut down on June 1, 2026",
    "gemini-2.0-flash-001": "Shut down on June 1, 2026",
    "gemini-2.0-flash-exp": "Experimental preview retired in 2025",
    "google/gemini-2.0-flash-exp:free": "Retired in 2025",
    "gemini-1.5-flash": "Shut down in September 2025",
    "gemini-1.5-pro": "Shut down in September 2025",
    "gemini-1.0-pro": "Shut down in early 2025",
    "llama-3.3-70b-versatile": "Retired on GroqCloud endpoints in 2026",
    "llama-3.1-8b-instant": "Retired on GroqCloud endpoints in 2026",
    "qwen-2.5-coder-32b": "Retired on GroqCloud endpoints in 2026",
    "text-davinci-003": "Shut down in January 2024",
    "gpt-3.5-turbo": "Deprecated legacy model",
}

PROHIBITED_KEY_FIELDS: set[str] = {
    "api_key",
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
    "groq_api_key",
    "openrouter_api_key",
    "user_api_key",
    "byok_key",
    "custom_api_key",
    "llm_key",
    "search_api_key",
    "authorization_key",
    "bearer_token",
    "api_token",
    "access_token",
    "secret_key",
}


def verify_zero_price_route(provider: str, model_id: str, price_per_token: float = 0.0) -> None:
    """Enforces the non-negotiable zero-price invariant. Rejects any route with non-zero pricing."""
    if price_per_token > 0.0:
        raise ZeroPriceViolationError(
            provider=provider,
            model_id=model_id,
            reason=f"Route has non-zero pricing (${price_per_token}/token). Only $0 routes are permitted.",
        )

    # Check for retired models
    if model_id.lower() in RETIRED_MODELS:
        detail = RETIRED_MODELS[model_id.lower()]
        raise ZeroPriceViolationError(
            provider=provider,
            model_id=model_id,
            reason=f"Model '{model_id}' is officially retired ({detail}) and cannot be invoked.",
        )

    provider_routes = VERIFIED_ZERO_PRICE_ROUTES.get(provider.lower())
    if not provider_routes or model_id not in provider_routes:
        # Check if model has explicit :free tag
        if not model_id.endswith(":free"):
            raise ZeroPriceViolationError(
                provider=provider,
                model_id=model_id,
                reason=f"Model '{model_id}' under provider '{provider}' is not an officially verified zero-price route.",
            )


def check_and_reject_byok(data: Any) -> None:
    """Detects and strictly rejects any user-supplied API key payload (dictionaries, lists, nested structures)."""
    if not data:
        return

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(key, str) and key.lower() in PROHIBITED_KEY_FIELDS:
                raise BYOKViolationError(
                    f"Prohibited field '{key}' detected. PromptIQ is 100% free; user API keys are strictly forbidden."
                )
            check_and_reject_byok(value)
    elif isinstance(data, list):
        for item in data:
            check_and_reject_byok(item)
