"""Capacity Governor, fair-use rate limiting, and circuit breaker."""

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from promptiq.core.config import settings
from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.core.logging import logger


class CapacityGovernor:
    """Enforces fair-use quotas, request de-duplication, concurrency caps, and circuit breakers."""

    def __init__(self):
        # Sliding window timestamps of user requests: user_id -> list of float timestamps
        self._user_requests: dict[str, list[float]] = defaultdict(list)

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


governor = CapacityGovernor()
