"""OpenRouter zero-price free variants adapter."""

import json
import time

import httpx

from promptiq.core.config import settings
from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.core.logging import logger
from promptiq.gateway.adapters.base import BaseInferenceAdapter
from promptiq.gateway.adapters.mock_adapter import MockInferenceAdapter
from promptiq.gateway.eligibility import verify_zero_price_route
from promptiq.gateway.governor import governor
from promptiq.gateway.models import InferenceRequest, InferenceResponse


class OpenRouterInferenceAdapter(BaseInferenceAdapter):
    """Adapter for OpenRouter free-tier models ($0 price tag)."""

    provider_name: str = "openrouter"
    model_id: str = "meta-llama/llama-3.3-70b-instruct:free"

    def __init__(self, model_id: str | None = None):
        if model_id:
            self.model_id = model_id
        verify_zero_price_route(self.provider_name, self.model_id, price_per_token=0.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        api_key = settings.OPERATOR_OPENROUTER_API_KEY
        if not api_key:
            if settings.MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK:
                logger.info("No operator OpenRouter API key set; falling back to deterministic mock adapter")
                mock = MockInferenceAdapter()
                mock.model_id = f"{self.model_id}-mock"
                return await mock.generate(request)
            raise CapacityExhaustedError("OpenRouter operator route is unconfigured.")

        governor.check_circuit_breaker(self.provider_name)

        start_time = time.perf_counter()
        url = "https://openrouter.ai/api/v1/chat/completions"

        messages = []
        if request.system_instruction:
            messages.append({"role": "system", "content": request.system_instruction})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://promptiq.internal",
                "X-Title": "PromptIQ",
            }
            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 429:
                    governor.trip_circuit_breaker(self.provider_name, "OpenRouter free rate limit exceeded", pause_duration_seconds=60)
                    raise CapacityExhaustedError("OpenRouter free tier limit reached. Pausing route.", retry_after=60)

                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                structured_data = None
                if request.response_schema:
                    try:
                        structured_data = json.loads(content)
                    except (json.JSONDecodeError, ValueError):
                        logger.debug("Failed to parse response schema JSON from OpenRouter output.")

                return InferenceResponse(
                    text=content,
                    structured_data=structured_data,
                    model_id=self.model_id,
                    provider=self.provider_name,
                    latency_ms=round(latency_ms, 2),
                    tokens_used=data.get("usage", {}).get("total_tokens", len(content) // 4),
                    route_cost=0.0,
                )
            except httpx.HTTPStatusError as e:
                governor.trip_circuit_breaker(self.provider_name, f"OpenRouter HTTP {e.response.status_code}")
                raise CapacityExhaustedError(f"OpenRouter API error: {e.response.status_code}", retry_after=30)
            except httpx.RequestError as e:
                governor.trip_circuit_breaker(self.provider_name, f"OpenRouter connection failure: {e}")
                raise CapacityExhaustedError(f"OpenRouter connection error: {e}", retry_after=30)
