"""Google Gemini Developer API zero-price free-tier adapter."""

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


class GeminiInferenceAdapter(BaseInferenceAdapter):
    """Adapter for Google Gemini Developer API free tier."""

    provider_name: str = "gemini"
    model_id: str = "gemini-3.8-flash"

    def __init__(self, model_id: str | None = None):
        if model_id:
            self.model_id = model_id
        verify_zero_price_route(self.provider_name, self.model_id, price_per_token=0.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        api_key = settings.effective_gemini_api_key
        if not api_key:
            if settings.MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK:
                logger.info("No operator Gemini API key set; falling back to deterministic mock adapter")
                mock = MockInferenceAdapter()
                mock.model_id = f"{self.model_id}-mock"
                return await mock.generate(request)
            raise CapacityExhaustedError("Gemini operator route is unconfigured (BLOCKED_EXTERNAL).")

        model_to_use = request.target_model_id or self.model_id
        verify_zero_price_route(self.provider_name, model_to_use, price_per_token=0.0)

        governor.check_circuit_breaker(self.provider_name)
        governor.check_model_quota(model_to_use)

        start_time = time.perf_counter()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_to_use}:generateContent?key={api_key}"

        # Construct Gemini contents payload
        contents = []
        for msg in request.messages:
            contents.append({"role": "user" if msg.role == "user" else "model", "parts": [{"text": msg.content}]})

        payload = {"contents": contents}
        if request.system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": request.system_instruction}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, json=payload)
                governor.inspect_response_headers(self.provider_name, self.model_id, resp.headers, resp.status_code)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("retry-after", 60))
                    raise CapacityExhaustedError("Gemini free tier rate limit reached. Pausing route.", retry_after=retry_after)

                resp.raise_for_status()
                data = resp.json()

                candidate = data["candidates"][0]["content"]["parts"][0]["text"]
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                structured_data = None
                if request.response_schema:
                    try:
                        structured_data = json.loads(candidate)
                    except (json.JSONDecodeError, ValueError):
                        logger.debug("Failed to deserialize response schema into structured JSON.")

                tokens_used = len(candidate) // 4
                governor.record_model_usage(model_to_use, tokens_used)

                return InferenceResponse(
                    text=candidate,
                    structured_data=structured_data,
                    model_id=model_to_use,
                    provider=self.provider_name,
                    latency_ms=round(latency_ms, 2),
                    tokens_used=tokens_used,
                    route_cost=0.0,
                )
            except httpx.HTTPStatusError as e:
                governor.trip_circuit_breaker(self.provider_name, f"Gemini HTTP {e.response.status_code}")
                raise CapacityExhaustedError(f"Gemini API error: {e.response.status_code}", retry_after=30)
            except httpx.RequestError as e:
                governor.trip_circuit_breaker(self.provider_name, f"Gemini connection failure: {e}")
                raise CapacityExhaustedError(f"Gemini connection error: {e}", retry_after=30)
