"""Capacity Governor, fair-use rate limiting, model-specific quotas, and circuit breaker."""

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from promptiq.core.config import settings
from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.core.logging import logger

# Official provider rate limits on free developer tiers (strictly non-paid)
MODEL_FREE_QUOTAS: dict[str, dict[str, int]] = {
    # Groq free tier per-model allowances (verified against Groq Console docs; developer-tier paid limits strictly excluded)
    "openai/gpt-oss-120b": {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 100000},
    "openai/gpt-oss-20b": {"rpm": 30, "rpd": 14400, "tpm": 6000, "tpd": 500000},
    "qwen/qwen3.8-27b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": 100000},
    # Google AI Studio Developer API free tier per-model allowances
    "gemini-3.8-flash": {"rpm": 15, "rpd": 1500, "tpm": 1000000, "tpd": 100000000},
    "gemini-3.5-flash-lite": {"rpm": 30, "rpd": 1500, "tpm": 1000000, "tpd": 100000000},
    "gemini-2.5-flash": {"rpm": 15, "rpd": 1500, "tpm": 1000000, "tpd": 100000000},
}


class CapacityGovernor:
    """Enforces fair-use quotas, request de-duplication, concurrency caps, and circuit breakers."""

    def __init__(self):
        # Sliding window timestamps of user requests: user_id -> list of float timestamps
        self._user_requests: dict[str, list[float]] = defaultdict(list)

        # Model-specific quota tracking: model_id -> list of timestamps / (timestamp, token_count)
        self._model_requests_minute: dict[str, list[float]] = defaultdict(list)
        self._model_requests_day: dict[str, list[float]] = defaultdict(list)
        self._model_tokens_minute: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._model_tokens_day: dict[str, list[tuple[float, int]]] = defaultdict(list)

        # Circuit breaker state: provider -> pause_until timestamp
        self._paused_until: dict[str, float] = {}
        self._pause_reasons: dict[str, str] = {}

        # Concurrency semaphore (lazily initialized on active event loop)
        self._concurrency_semaphore: asyncio.Semaphore | None = None

        # De-duplication cache: hash -> (timestamp, response)
        self._dedup_cache: dict[str, tuple[float, Any]] = {}
        self._dedup_window_seconds = 5.0

    @property
    def concurrency_semaphore(self) -> asyncio.Semaphore:
        """Lazily binds concurrency semaphore to the running asyncio event loop."""
        if self._concurrency_semaphore is None:
            self._concurrency_semaphore = asyncio.Semaphore(settings.RATE_LIMIT_GLOBAL_CONCURRENCY)
        return self._concurrency_semaphore

    def check_user_fair_use(self, user_id: str) -> None:
        """Enforces sliding-window rate limit per user."""
        if not settings.CAPACITY_GOVERNOR_ENABLED or user_id == "system":
            return

        now = datetime.now(UTC).timestamp()
        cutoff = now - 3600.0  # 1 hour window

        # Prune old timestamps
        recent = [t for t in self._user_requests[user_id] if t > cutoff]
        self._user_requests[user_id] = recent

        max_limit = settings.RATE_LIMIT_USER_REQUESTS_PER_HOUR
        if len(recent) >= max_limit:
            oldest_active = recent[0]
            retry_after = max(1, int(3600 - (now - oldest_active)))
            logger.warning("User fair-use rate limit exceeded", extra={"user_id": user_id, "retry_after": retry_after})
            raise CapacityExhaustedError(
                message=f"Fair-use limit of {max_limit} requests/hour reached. Please wait before submitting more tasks.",
                retry_after=retry_after,
            )

        self._user_requests[user_id].append(now)

    def check_model_quota(self, model_id: str, estimated_tokens: int = 1000) -> None:
        """Checks model-specific RPM, RPD, TPM, and TPD quotas against official provider boundaries."""
        quota = MODEL_FREE_QUOTAS.get(model_id)
        if not quota:
            return

        now = datetime.now(UTC).timestamp()
        minute_cutoff = now - 60.0
        day_cutoff = now - 86400.0

        # Prune minute requests
        recent_req_min = [t for t in self._model_requests_minute[model_id] if t > minute_cutoff]
        self._model_requests_minute[model_id] = recent_req_min
        if len(recent_req_min) >= quota.get("rpm", 30):
            oldest = recent_req_min[0]
            retry_after = max(1, int(60 - (now - oldest)))
            raise CapacityExhaustedError(
                message=f"Model '{model_id}' reached free tier rate limit ({quota['rpm']} RPM).",
                retry_after=retry_after,
                details={"model_id": model_id, "limit": "rpm", "cap": quota["rpm"]},
            )

        # Prune daily requests
        recent_req_day = [t for t in self._model_requests_day[model_id] if t > day_cutoff]
        self._model_requests_day[model_id] = recent_req_day
        if len(recent_req_day) >= quota.get("rpd", 1000):
            oldest = recent_req_day[0]
            retry_after = max(1, int(86400 - (now - oldest)))
            raise CapacityExhaustedError(
                message=f"Model '{model_id}' reached daily request ceiling ({quota['rpd']} RPD).",
                retry_after=retry_after,
                details={"model_id": model_id, "limit": "rpd", "cap": quota["rpd"]},
            )

        # Prune minute tokens
        recent_tok_min = [(t, tok) for t, tok in self._model_tokens_minute[model_id] if t > minute_cutoff]
        self._model_tokens_minute[model_id] = recent_tok_min
        tok_sum_min = sum(tok for _, tok in recent_tok_min)
        if tok_sum_min + estimated_tokens > quota.get("tpm", 12000):
            raise CapacityExhaustedError(
                message=f"Model '{model_id}' reached token rate limit ({quota['tpm']} TPM).",
                retry_after=max(1, int(60 - (now - recent_tok_min[0][0]))) if recent_tok_min else 60,
                details={"model_id": model_id, "limit": "tpm", "cap": quota["tpm"]},
            )

        # Prune daily tokens
        recent_tok_day = [(t, tok) for t, tok in self._model_tokens_day[model_id] if t > day_cutoff]
        self._model_tokens_day[model_id] = recent_tok_day
        tok_sum_day = sum(tok for _, tok in recent_tok_day)
        if tok_sum_day + estimated_tokens > quota.get("tpd", 100000):
            raise CapacityExhaustedError(
                message=f"Model '{model_id}' reached daily token ceiling ({quota['tpd']} TPD).",
                retry_after=max(1, int(86400 - (now - recent_tok_day[0][0]))) if recent_tok_day else 86400,
                details={"model_id": model_id, "limit": "tpd", "cap": quota["tpd"]},
            )

    def record_model_usage(self, model_id: str, tokens_used: int) -> None:
        """Records actual request timestamp and token usage for model-specific quota tracking."""
        now = datetime.now(UTC).timestamp()
        self._model_requests_minute[model_id].append(now)
        self._model_requests_day[model_id].append(now)
        self._model_tokens_minute[model_id].append((now, tokens_used))
        self._model_tokens_day[model_id].append((now, tokens_used))

    def inspect_response_headers(
        self, provider: str, model_id: str, headers: dict[str, str] | Any, status_code: int = 200
    ) -> None:
        """Inspects official provider response headers (Groq, Gemini) for rate limits and 429 retries."""
        header_map = {k.lower(): v for k, v in headers.items()} if hasattr(headers, "items") else {}

        # 1. Handle HTTP 429 or explicit retry-after
        if status_code == 429 or "retry-after" in header_map:
            retry_val = header_map.get("retry-after", "60")
            try:
                pause_sec = int(float(retry_val))
            except (ValueError, TypeError):
                pause_sec = 60
            pause_sec = max(5, pause_sec)
            self.trip_circuit_breaker(
                provider,
                reason=f"Provider {provider} returned 429 rate limit (model: {model_id})",
                pause_duration_seconds=pause_sec,
            )
            return

        # 2. Check remaining requests / tokens from Groq rate limit headers
        remaining_req = header_map.get("x-ratelimit-remaining-requests")
        if remaining_req is not None:
            try:
                if int(remaining_req) <= 0:
                    reset_time_str = header_map.get("x-ratelimit-reset-requests", "60s")
                    pause_sec = 60
                    self.trip_circuit_breaker(
                        provider,
                        reason=f"Provider quota exhausted (0 remaining requests, resets: {reset_time_str})",
                        pause_duration_seconds=pause_sec,
                    )
            except (ValueError, TypeError):
                pass

        remaining_tokens = header_map.get("x-ratelimit-remaining-tokens")
        if remaining_tokens is not None:
            try:
                if int(remaining_tokens) < 500:
                    self.trip_circuit_breaker(
                        provider,
                        reason=f"Provider token quota critical ({remaining_tokens} tokens remaining)",
                        pause_duration_seconds=30,
                    )
            except (ValueError, TypeError):
                pass

    def check_circuit_breaker(self, provider: str) -> None:
        """Checks if the provider is currently paused due to upstream quota exhaustion."""
        now = datetime.now(UTC).timestamp()
        pause_until = self._paused_until.get(provider, 0.0)

        if now < pause_until:
            retry_after = max(1, int(pause_until - now))
            reason = self._pause_reasons.get(provider, "Upstream capacity exhausted")
            raise CapacityExhaustedError(
                message=f"Route '{provider}' is temporarily paused ({reason}). Your request is queued/held.",
                retry_after=retry_after,
                details={"provider": provider, "reason": reason},
            )

    def trip_circuit_breaker(self, provider: str, reason: str, pause_duration_seconds: int = 60) -> None:
        """Pauses a provider route upon detecting upstream 429/503 errors."""
        now = datetime.now(UTC).timestamp()
        self._paused_until[provider] = now + pause_duration_seconds
        self._pause_reasons[provider] = reason
        logger.error(
            f"Circuit breaker tripped for provider '{provider}': {reason}. Paused for {pause_duration_seconds}s."
        )

    def check_deduplication(self, request_payload: dict[str, Any]) -> Any | None:
        """Returns cached response if an identical request was made within the deduplication window."""
        payload_str = json.dumps(request_payload, sort_keys=True)
        req_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        now = datetime.now(UTC).timestamp()

        if req_hash in self._dedup_cache:
            ts, cached_response = self._dedup_cache[req_hash]
            if now - ts < self._dedup_window_seconds:
                logger.info("Serving deduplicated response from cache")
                return cached_response

        return None

    def store_deduplication(self, request_payload: dict[str, Any], response: Any) -> None:
        """Stores response in short-lived deduplication cache."""
        payload_str = json.dumps(request_payload, sort_keys=True)
        req_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        now = datetime.now(UTC).timestamp()
        self._dedup_cache[req_hash] = (now, response)

    def get_remaining_user_requests(self, user_id: str) -> int:
        now = datetime.now(UTC).timestamp()
        cutoff = now - 3600.0
        recent = [t for t in self._user_requests[user_id] if t > cutoff]
        return max(0, settings.RATE_LIMIT_USER_REQUESTS_PER_HOUR - len(recent))

    def get_model_quota_status(self, model_id: str) -> dict[str, Any]:
        """Returns current consumption metrics for a specific model."""
        now = datetime.now(UTC).timestamp()
        min_cutoff = now - 60.0
        day_cutoff = now - 86400.0
        req_min = len([t for t in self._model_requests_minute[model_id] if t > min_cutoff])
        req_day = len([t for t in self._model_requests_day[model_id] if t > day_cutoff])
        tok_min = sum(tok for t, tok in self._model_tokens_minute[model_id] if t > min_cutoff)
        tok_day = sum(tok for t, tok in self._model_tokens_day[model_id] if t > day_cutoff)
        quota = MODEL_FREE_QUOTAS.get(model_id, {})
        return {
            "model_id": model_id,
            "requests_last_minute": req_min,
            "rpm_limit": quota.get("rpm"),
            "requests_last_24h": req_day,
            "rpd_limit": quota.get("rpd"),
            "tokens_last_minute": tok_min,
            "tpm_limit": quota.get("tpm"),
            "tokens_last_24h": tok_day,
            "tpd_limit": quota.get("tpd"),
        }


governor = CapacityGovernor()
capacity_governor = governor

