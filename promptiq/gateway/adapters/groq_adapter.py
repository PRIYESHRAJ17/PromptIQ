"""Groq free-tier inference adapter."""

import json
import time
from datetime import UTC, datetime

import httpx

from promptiq.core.config import settings
from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.core.logging import logger
from promptiq.gateway.adapters.base import BaseInferenceAdapter
from promptiq.gateway.adapters.mock_adapter import MockInferenceAdapter
from promptiq.gateway.eligibility import verify_zero_price_route
from promptiq.gateway.governor import governor
from promptiq.gateway.models import InferenceRequest, InferenceResponse


class GroqInferenceAdapter(BaseInferenceAdapter):
    """Adapter for Groq free plan."""

    provider_name: str = "groq"
    model_id: str = "openai/gpt-oss-120b"

    def __init__(self, model_id: str | None = None):
        if model_id:
            self.model_id = model_id
        verify_zero_price_route(self.provider_name, self.model_id, price_per_token=0.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        api_key = settings.effective_groq_api_key
        if not api_key:
            if settings.MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK:
                logger.info("No operator Groq API key set; falling back to deterministic mock adapter")
                mock = MockInferenceAdapter()
                mock.model_id = f"{self.model_id}-mock"
                return await mock.generate(request)
            raise CapacityExhaustedError("Groq operator route is unconfigured (BLOCKED_EXTERNAL).")

        model_to_use = request.target_model_id or self.model_id
        verify_zero_price_route(self.provider_name, model_to_use, price_per_token=0.0)

        governor.check_circuit_breaker(self.provider_name)
        governor.check_model_quota(model_to_use)

        request_time = datetime.now(UTC).isoformat()
        start_time = time.perf_counter()
        url = "https://api.groq.com/openai/v1/chat/completions"

        messages = []
        if request.system_instruction:
            messages.append({"role": "system", "content": request.system_instruction})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or 4096,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            try:
                resp = await client.post(url, json=payload, headers=headers)
                response_time = datetime.now(UTC).isoformat()
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                req_id = resp.headers.get("x-request-id")
                rate_limit_headers = {
                    "limit_requests": resp.headers.get("x-ratelimit-limit-requests"),
                    "limit_tokens": resp.headers.get("x-ratelimit-limit-tokens"),
                    "remaining_requests": resp.headers.get("x-ratelimit-remaining-requests"),
                    "remaining_tokens": resp.headers.get("x-ratelimit-remaining-tokens"),
                    "reset_requests": resp.headers.get("x-ratelimit-reset-requests"),
                    "reset_tokens": resp.headers.get("x-ratelimit-reset-tokens"),
                }

                # Inspect Groq rate-limit headers (RPM/RPD/TPM/TPD and retry-after)
                governor.inspect_response_headers(self.provider_name, model_to_use, resp.headers, resp.status_code)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("retry-after", 60))
                    raise CapacityExhaustedError("Groq free tier rate limit reached. Route paused.", retry_after=retry_after)

                resp.raise_for_status()
                data = resp.json()
                req_id = req_id or data.get("id")
                content = data["choices"][0]["message"]["content"]

                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens", len(content) // 4)
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                governor.record_model_usage(model_to_use, tokens_used)

                structured_data = None
                if request.response_schema:
                    try:
                        structured_data = json.loads(content)
                    except (json.JSONDecodeError, ValueError):
                        logger.debug("Failed to parse response schema JSON from Groq output.")

                return InferenceResponse(
                    text=content,
                    structured_data=structured_data,
                    model_id=model_to_use,
                    provider=self.provider_name,
                    latency_ms=round(latency_ms, 2),
                    tokens_used=tokens_used,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    route_cost=0.0,
                    request_id=req_id,
                    http_status=resp.status_code,
                    rate_limit_headers=rate_limit_headers,
                    request_timestamp=request_time,
                    response_timestamp=response_time,
                )
            except httpx.HTTPStatusError as e:
                governor.trip_circuit_breaker(self.provider_name, f"Groq HTTP {e.response.status_code}")
                raise CapacityExhaustedError(f"Groq API error: {e.response.status_code}", retry_after=30)
            except httpx.RequestError as e:
                governor.trip_circuit_breaker(self.provider_name, f"Groq connection failure: {e}")
                raise CapacityExhaustedError(f"Groq connection error: {e}", retry_after=30)
