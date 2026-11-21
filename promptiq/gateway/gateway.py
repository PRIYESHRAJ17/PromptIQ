"""Central Managed Zero-Price Inference Gateway."""

from promptiq.core.config import settings
from promptiq.core.exceptions import ZeroPriceViolationError
from promptiq.core.logging import logger
from promptiq.gateway.adapters import (
    BaseInferenceAdapter,
    GeminiInferenceAdapter,
    GroqInferenceAdapter,
    MockInferenceAdapter,
    OpenRouterInferenceAdapter,
)
from promptiq.gateway.eligibility import verify_zero_price_route
from promptiq.gateway.governor import governor
from promptiq.gateway.models import InferenceRequest, InferenceResponse
from promptiq.schemas.governor import QuotaStatusResponse


class InferenceGateway:
    """Coordinates centrally hosted zero-price model routing, fair-use gating, and test mocking."""

    def __init__(self):
        self._adapters: dict[str, BaseInferenceAdapter] = {
            "mock": MockInferenceAdapter(),
            "gemini": GeminiInferenceAdapter(),
            "groq": GroqInferenceAdapter(),
            "openrouter": OpenRouterInferenceAdapter(),
        }

    def get_adapter(self, provider: str | None = None) -> BaseInferenceAdapter:
        """Resolves the configured zero-price provider adapter."""
        route = (provider or settings.MANAGED_INFERENCE_PRIMARY_ROUTE).lower()
        if route not in self._adapters:
            logger.warning(f"Requested route '{route}' not found. Defaulting to 'mock'.")
            route = "mock"

        adapter = self._adapters[route]
        # Invariant check: verify route eligibility
        verify_zero_price_route(adapter.provider_name, adapter.model_id, price_per_token=0.0)
        return adapter

    async def generate(self, request: InferenceRequest, provider: str | None = None) -> InferenceResponse:
        """Executes inference through the centrally managed zero-price gateway."""
        # 1. Enforce user fair-use limits
        governor.check_user_fair_use(request.user_id)

        # 2. Check de-duplication cache
        cache_key_payload = {
            "messages": [m.model_dump() for m in request.messages],
            "system_instruction": request.system_instruction,
            "task_context": request.task_context,
            "provider": provider or settings.MANAGED_INFERENCE_PRIMARY_ROUTE,
        }
        cached = governor.check_deduplication(cache_key_payload)
        if cached is not None:
            return cached

        # 3. Resolve adapter
        adapter = self.get_adapter(provider)

        # 4. Execute generation with concurrency control
        async with governor._concurrency_semaphore:
            response = await adapter.generate(request)

        # 5. Invariant Assertion: Route cost MUST be 0.0
        if response.route_cost > 0.0:
            raise ZeroPriceViolationError(
                provider=response.provider,
                model_id=response.model_id,
                reason="Inference response returned non-zero route cost.",
            )

        # 6. Store in deduplication cache
        governor.store_deduplication(cache_key_payload, response)

        return response

    def get_quota_status(self, user_id: str = "anonymous") -> QuotaStatusResponse:
        """Returns current status of the managed inference service."""
        active_route = settings.MANAGED_INFERENCE_PRIMARY_ROUTE
        is_paused = active_route in governor._paused_until
        pause_reason = governor._pause_reasons.get(active_route) if is_paused else None

        return QuotaStatusResponse(
            provider=active_route,
            is_paused=is_paused,
            pause_reason=pause_reason,
            minute_requests_used=len(governor._user_requests.get(user_id, [])),
            daily_requests_used=len(governor._user_requests.get(user_id, [])),
            user_requests_remaining_this_hour=governor.get_remaining_user_requests(user_id),
            zero_price_policy_active=True,
            notice="PromptIQ is 100% free. No user billing or API keys required.",
        )


inference_gateway = InferenceGateway()
