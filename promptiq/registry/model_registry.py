"""Model Registry service and curated entries."""

from typing import Any

from promptiq.schemas.registry import ModelRecordSchema

# Baseline curated Model Registry entries
CURATED_MODELS: list[dict[str, Any]] = [
    {
        "id": "gemini-2.0-flash",
        "provider": "google",
        "model_id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "context_window": 1048576,
        "output_limit": 8192,
        "supports_tools": True,
        "supports_structured_output": True,
        "cutoff_date": "2024-08",
        "release_date": "2024-12",
        "is_zero_price": True,
        "rate_limits": {"rpm": 15, "rpd": 1500, "tpm": 1000000},
        "confidence": "provider_documented",
        "source_url": "https://ai.google.dev/gemini-api/docs/pricing",
    },
    {
        "id": "gemini-1.5-flash",
        "provider": "google",
        "model_id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "context_window": 1048576,
        "output_limit": 8192,
        "supports_tools": True,
        "supports_structured_output": True,
        "cutoff_date": "2024-04",
        "release_date": "2024-05",
        "is_zero_price": True,
        "rate_limits": {"rpm": 15, "rpd": 1500, "tpm": 1000000},
        "confidence": "provider_documented",
        "source_url": "https://ai.google.dev/gemini-api/docs/pricing",
    },
    {
        "id": "llama-3.3-70b-versatile",
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B Versatile (Groq)",
        "context_window": 131072,
        "output_limit": 4096,
        "supports_tools": True,
        "supports_structured_output": True,
        "cutoff_date": "2023-12",
        "release_date": "2024-12",
        "is_zero_price": True,
        "rate_limits": {"rpm": 30, "rpd": 1000, "tpm": 12000},
        "confidence": "provider_documented",
        "source_url": "https://console.groq.com/docs/rate-limits",
    },
    {
        "id": "claude-3-7-sonnet",
        "provider": "anthropic",
        "model_id": "claude-3-7-sonnet-20250219",
        "name": "Claude 3.7 Sonnet (Hybrid Thinking)",
        "context_window": 200000,
        "output_limit": 8192,
        "supports_tools": True,
        "supports_structured_output": True,
        "cutoff_date": "2024-11",
        "release_date": "2025-02",
        "is_zero_price": False,  # Target model only, not for PromptIQ internal zero-price inference
        "rate_limits": {},
        "confidence": "provider_documented",
        "source_url": "https://platform.claude.com/docs/en/models/overview",
    },
    {
        "id": "gpt-4o",
        "provider": "openai",
        "model_id": "gpt-4o",
        "name": "GPT-4o Omnimodal",
        "context_window": 128000,
        "output_limit": 16384,
        "supports_tools": True,
        "supports_structured_output": True,
        "cutoff_date": "2023-10",
        "release_date": "2024-05",
        "is_zero_price": False,  # Target model only
        "rate_limits": {},
        "confidence": "provider_documented",
        "source_url": "https://platform.openai.com/docs/models",
    },
]


class ModelRegistryService:
    """Provides querying and filtering of models by provider, capabilities, and zero-price status."""

    @staticmethod
    def list_models(zero_price_only: bool = False) -> list[ModelRecordSchema]:
        results = []
        for m in CURATED_MODELS:
            if zero_price_only and not m["is_zero_price"]:
                continue
            results.append(ModelRecordSchema(**m))
        return results

    @staticmethod
    def get_model(model_id: str) -> ModelRecordSchema | None:
        for m in CURATED_MODELS:
            if m["model_id"] == model_id or m["id"] == model_id:
                return ModelRecordSchema(**m)
        return None
