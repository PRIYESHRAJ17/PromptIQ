"""Capacity Governor, fair-use rate limiting, model-specific quotas, and circuit breaker."""

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from promptiq.core.config import settings
from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.core.logging import logger

DEFAULT_QUOTA_LEDGER_PATH = Path("data/quota_ledger.json")

# Official provider rate limits on free developer tiers (strictly non-paid)
MODEL_FREE_QUOTAS: dict[str, dict[str, int]] = {
    # Groq free tier per-model allowances (verified against Groq Console docs and live headers; developer-tier paid limits strictly excluded)
    "openai/gpt-oss-120b": {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 100000},
    "openai/gpt-oss-20b": {"rpm": 30, "rpd": 14400, "tpm": 8000, "tpd": 500000},
    "qwen/qwen3.8-27b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": 100000},
    # Google AI Studio Developer API free tier per-model allowances
    "gemini-3.8-flash": {"rpm": 15, "rpd": 1500, "tpm": 1000000, "tpd": 100000000},
    "gemini-3.5-flash-lite": {"rpm": 30, "rpd": 1500, "tpm": 1000000, "tpd": 100000000},
    "gemini-2.5-flash": {"rpm": 15, "rpd": 1500, "tpm": 1000000, "tpd": 100000000},
}


class CapacityGovernor:
    """Enforces fair-use quotas, request de-duplication, concurrency caps, circuit breakers, and durable quota ledger."""

    def __init__(self, ledger_path: Path | str | None = None, auto_load: bool = True):
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

        # Durable quota ledger path and last provider headers
        self._ledger_path: Path = Path(ledger_path) if ledger_path else DEFAULT_QUOTA_LEDGER_PATH
        self._auto_load: bool = auto_load
        self._last_provider_headers: dict[str, dict[str, Any]] = {}

        # Auto-load durable state across processes when not in clean test mode (or when explicitly requested)
        if auto_load and (ledger_path is not None or (not settings.is_test and self._ledger_path.exists())):
            self.load_durable_state()

    @property
    def concurrency_semaphore(self) -> asyncio.Semaphore:
        """Lazily binds concurrency semaphore to the running asyncio event loop."""
        if self._concurrency_semaphore is None:
            self._concurrency_semaphore = asyncio.Semaphore(settings.RATE_LIMIT_GLOBAL_CONCURRENCY)
        return self._concurrency_semaphore

    def load_durable_state(self, path: Path | str | None = None) -> bool:
        """Loads and prunes persisted quota telemetry from the durable ledger file."""
        target_path = Path(path) if path else self._ledger_path
        if not target_path.exists():
            return False

        try:
            with open(target_path, encoding="utf-8") as f:
                data = json.load(f)

            now = datetime.now(UTC).timestamp()
            minute_cutoff = now - 60.0
            day_cutoff = now - 86400.0

            # Prune and merge minute requests
            for model_id, timestamps in data.get("model_requests_minute", {}).items():
                active = [t for t in timestamps if t > minute_cutoff]
                merged_req = sorted(set(self._model_requests_minute[model_id] + active))
                self._model_requests_minute[model_id] = merged_req

            # Prune and merge daily requests
            for model_id, timestamps in data.get("model_requests_day", {}).items():
                active = [t for t in timestamps if t > day_cutoff]
                merged_day = sorted(set(self._model_requests_day[model_id] + active))
                self._model_requests_day[model_id] = merged_day

            # Prune and merge minute tokens
            for model_id, token_records in data.get("model_tokens_minute", {}).items():
                active = [(t, tok) for t, tok in token_records if t > minute_cutoff]
                merged_tok = sorted(set(self._model_tokens_minute[model_id] + active), key=lambda x: x[0])
                self._model_tokens_minute[model_id] = merged_tok

            # Prune and merge daily tokens
            for model_id, token_records in data.get("model_tokens_day", {}).items():
                active = [(t, tok) for t, tok in token_records if t > day_cutoff]
                merged_tok_day = sorted(set(self._model_tokens_day[model_id] + active), key=lambda x: x[0])
                self._model_tokens_day[model_id] = merged_tok_day

            # Restore paused providers
            for provider, pause_until in data.get("paused_until", {}).items():
                if pause_until > now:
                    self._paused_until[provider] = pause_until

            for provider, reason in data.get("pause_reasons", {}).items():
                self._pause_reasons[provider] = reason

            # Restore last provider headers
            self._last_provider_headers.update(data.get("last_provider_headers", {}))
            return True
        except Exception as e:
            logger.warning("Failed to load durable quota ledger from %s: %s", target_path, e)
            return False

    def save_durable_state(self, path: Path | str | None = None) -> bool:
        """Flushes current quota tracking state to the durable ledger file atomically."""
        target_path = Path(path) if path else self._ledger_path
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "updated_at": datetime.now(UTC).isoformat(),
                "model_requests_minute": dict(self._model_requests_minute),
                "model_requests_day": dict(self._model_requests_day),
                "model_tokens_minute": dict(self._model_tokens_minute),
                "model_tokens_day": dict(self._model_tokens_day),
                "paused_until": self._paused_until,
                "pause_reasons": self._pause_reasons,
                "last_provider_headers": self._last_provider_headers,
            }
            tmp_path = target_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            tmp_path.replace(target_path)
            return True
        except Exception as e:
            logger.warning("Failed to save durable quota ledger to %s: %s", target_path, e)
            return False

    def sync_from_execution_ledger(self, ledger_path: Path | str) -> dict[str, Any]:
        """Reconstructs and persists governor usage state directly from a workflow results JSON ledger."""
        path = Path(ledger_path)
        if not path.exists():
            return {"status": "not_found", "path": str(path)}

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.warning("Failed to read workflow execution ledger %s: %s", path, e)
            return {"status": "read_error", "error": str(e)}

        summary = data.get("summary", {})
        steps = summary.get("steps", [])
        synced_count = 0

        for step in steps:
            model_id = step.get("model_id")
            if not model_id or model_id == "deterministic-verifier-v1":
                continue

            ts_str = step.get("timestamp")
            if not ts_str:
                continue

            try:
                r_clean = ts_str[:-1] + "+00:00" if ts_str.endswith("Z") else ts_str
                ts = datetime.fromisoformat(r_clean).timestamp()
            except (ValueError, TypeError) as ts_err:
                logger.debug("Skipping unparseable timestamp '%s': %s", ts_str, ts_err)
                continue

            inp = step.get("input_tokens", 0)
            out = step.get("output_tokens", 0)
            total = inp + out

            # Only genuine successful HTTP steps count against quota usage
            if total > 0 and step.get("http_status") == 200:
                self._model_requests_minute[model_id].append(ts)
                self._model_requests_day[model_id].append(ts)
                self._model_tokens_minute[model_id].append((ts, total))
                self._model_tokens_day[model_id].append((ts, total))
                synced_count += 1

            meta = step.get("metadata", {})
            hdrs = meta.get("rate_limit_headers")
            if hdrs and isinstance(hdrs, dict):
                self._last_provider_headers[model_id] = {
                    "headers": hdrs,
                    "response_timestamp": meta.get("response_timestamp", ts_str),
                    "recorded_at": ts,
                }

        self.save_durable_state()
        return {
            "status": "synced",
            "synced_steps": synced_count,
            "models": list(self._last_provider_headers.keys()),
        }

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
        """Checks model-specific RPM, RPD, TPM, and TPD quotas against official provider boundaries and durable telemetry."""
        quota = MODEL_FREE_QUOTAS.get(model_id)
        if not quota:
            return

        # Ensure latest cross-process state is reflected
        if self._auto_load and (not settings.is_test or str(self._ledger_path) != str(DEFAULT_QUOTA_LEDGER_PATH)):
            self.load_durable_state()

        now = datetime.now(UTC).timestamp()
        minute_cutoff = now - 60.0
        day_cutoff = now - 86400.0

        # Check last provider response header for pending reset duration
        hdr_info = self._last_provider_headers.get(model_id)
        if hdr_info:
            hdrs = hdr_info.get("headers", {})
            reset_tokens_str = hdrs.get("reset_tokens") or hdrs.get("x-ratelimit-reset-tokens")
            resp_ts_str = hdr_info.get("response_timestamp")
            recorded_at = hdr_info.get("recorded_at")

            if reset_tokens_str:
                hdr_reset_duration = self.parse_rate_limit_reset_seconds(reset_tokens_str)
                if resp_ts_str:
                    try:
                        r_clean = resp_ts_str[:-1] + "+00:00" if resp_ts_str.endswith("Z") else resp_ts_str
                        resp_ts = datetime.fromisoformat(r_clean).timestamp()
                    except Exception:
                        resp_ts = recorded_at or now
                else:
                    resp_ts = recorded_at or now

                time_since_resp = now - resp_ts
                if time_since_resp < hdr_reset_duration:
                    time_left = max(1, int(round(hdr_reset_duration - time_since_resp)))
                    rem_tokens_hdr = hdrs.get("remaining_tokens") or hdrs.get("x-ratelimit-remaining-tokens")
                    if rem_tokens_hdr is not None:
                        try:
                            if int(rem_tokens_hdr) < estimated_tokens:
                                raise CapacityExhaustedError(
                                    message=f"Model '{model_id}' upstream quota pending reset ({rem_tokens_hdr} tokens left in header, required {estimated_tokens}). Resets in {time_left}s.",
                                    retry_after=time_left,
                                    details={"model_id": model_id, "limit": "provider_header_tpm", "retry_after": time_left},
                                )
                        except ValueError:
                            pass

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
        tpm_limit = quota.get("tpm", 8000)
        if tok_sum_min + estimated_tokens > tpm_limit:
            retry_after = max(1, int(60 - (now - recent_tok_min[0][0]))) if recent_tok_min else 60
            raise CapacityExhaustedError(
                message=f"Model '{model_id}' reached token rate limit ({tpm_limit} TPM). Required: {estimated_tokens}, Used in window: {tok_sum_min}/{tpm_limit} TPM.",
                retry_after=retry_after,
                details={
                    "model_id": model_id,
                    "limit": "tpm",
                    "cap": tpm_limit,
                    "tpm_used": tok_sum_min,
                    "tpm_remaining": max(0, tpm_limit - tok_sum_min),
                    "estimated_tokens": estimated_tokens,
                    "retry_after": retry_after,
                },
            )

        # Prune daily tokens
        recent_tok_day = [(t, tok) for t, tok in self._model_tokens_day[model_id] if t > day_cutoff]
        self._model_tokens_day[model_id] = recent_tok_day
        tok_sum_day = sum(tok for _, tok in recent_tok_day)
        if tok_sum_day + estimated_tokens > quota.get("tpd", 100000):
            retry_after = max(1, int(86400 - (now - recent_tok_day[0][0]))) if recent_tok_day else 86400
            raise CapacityExhaustedError(
                message=f"Model '{model_id}' reached daily token ceiling ({quota['tpd']} TPD).",
                retry_after=retry_after,
                details={"model_id": model_id, "limit": "tpd", "cap": quota["tpd"], "tpd_used": tok_sum_day, "retry_after": retry_after},
            )

    def get_model_quota_status(self, model_id: str) -> dict[str, Any]:
        """Returns real-time sliding-window quota usage, capacity, and reset times for a model."""
        if self._auto_load and (not settings.is_test or str(self._ledger_path) != str(DEFAULT_QUOTA_LEDGER_PATH)):
            self.load_durable_state()

        quota = MODEL_FREE_QUOTAS.get(model_id, {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 100000})
        now = datetime.now(UTC).timestamp()
        minute_cutoff = now - 60.0
        day_cutoff = now - 86400.0

        recent_req_min = [t for t in self._model_requests_minute[model_id] if t > minute_cutoff]
        recent_req_day = [t for t in self._model_requests_day[model_id] if t > day_cutoff]
        recent_tok_min = [(t, tok) for t, tok in self._model_tokens_minute[model_id] if t > minute_cutoff]
        recent_tok_day = [(t, tok) for t, tok in self._model_tokens_day[model_id] if t > day_cutoff]

        tok_sum_min = sum(tok for _, tok in recent_tok_min)
        tok_sum_day = sum(tok for _, tok in recent_tok_day)
        req_count_min = len(recent_req_min)
        req_count_day = len(recent_req_day)

        tpm_limit = quota.get("tpm", 8000)
        rpm_limit = quota.get("rpm", 30)
        tpd_limit = quota.get("tpd", 100000)
        rpd_limit = quota.get("rpd", 1000)

        tpm_remaining = max(0, tpm_limit - tok_sum_min)
        rpm_remaining = max(0, rpm_limit - req_count_min)

        reset_seconds = 0.0
        if recent_tok_min:
            oldest_ts = min([recent_tok_min[0][0]] + ([recent_req_min[0]] if recent_req_min else []))
            time_since_oldest = now - oldest_ts
            if time_since_oldest < 60.0:
                reset_seconds = max(0.0, round(60.0 - time_since_oldest, 2))

        # Check last provider response header telemetry for pending reset
        hdr_info = self._last_provider_headers.get(model_id)
        if hdr_info:
            hdrs = hdr_info.get("headers", {})
            reset_tokens_str = hdrs.get("reset_tokens") or hdrs.get("x-ratelimit-reset-tokens")
            resp_ts_str = hdr_info.get("response_timestamp")
            recorded_at = hdr_info.get("recorded_at")

            if reset_tokens_str:
                hdr_reset_duration = self.parse_rate_limit_reset_seconds(reset_tokens_str)
                if resp_ts_str:
                    try:
                        r_clean = resp_ts_str[:-1] + "+00:00" if resp_ts_str.endswith("Z") else resp_ts_str
                        resp_ts = datetime.fromisoformat(r_clean).timestamp()
                    except Exception:
                        resp_ts = recorded_at or now
                else:
                    resp_ts = recorded_at or now

                time_since_resp = now - resp_ts
                if time_since_resp < hdr_reset_duration:
                    time_left = round(hdr_reset_duration - time_since_resp, 2)
                    reset_seconds = max(reset_seconds, time_left)

        is_rate_limited = (
            tok_sum_min >= tpm_limit
            or req_count_min >= rpm_limit
            or (reset_seconds > 0.0 and tok_sum_min > 0)
        )

        return {
            "model_id": model_id,
            "requests_last_minute": req_count_min,
            "rpm_used": req_count_min,
            "rpm_limit": rpm_limit,
            "rpm_remaining": rpm_remaining,
            "requests_last_24h": req_count_day,
            "rpd_limit": rpd_limit,
            "tokens_last_minute": tok_sum_min,
            "tpm_used": tok_sum_min,
            "tpm_limit": tpm_limit,
            "tpm_remaining": tpm_remaining,
            "tokens_last_24h": tok_sum_day,
            "tpd_limit": tpd_limit,
            "reset_seconds": reset_seconds,
            "is_rate_limited": is_rate_limited,
        }

    @staticmethod
    def parse_rate_limit_reset_seconds(reset_str: str | None) -> float:
        """Parses rate limit reset strings like '26.752s', '1m26.4s', or '60s' into float seconds."""
        if not reset_str:
            return 0.0
        s = reset_str.strip().lower()
        import re
        m_match = re.match(r"^(?:(\d+(?:\.\d+)?)m)?(?:(\d+(?:\.\d+)?)s)?$", s)
        if m_match:
            mins = float(m_match.group(1) or 0)
            secs = float(m_match.group(2) or 0)
            return round(mins * 60.0 + secs, 2)
        try:
            return float(s.rstrip("s"))
        except ValueError:
            return 0.0

    def record_model_usage(
        self,
        model_id: str,
        tokens_used: int,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        timestamp: float | None = None,
    ) -> None:
        """Records actual request timestamp and token usage for model-specific quota tracking."""
        now = timestamp if timestamp is not None else datetime.now(UTC).timestamp()
        self._model_requests_minute[model_id].append(now)
        self._model_requests_day[model_id].append(now)
        self._model_tokens_minute[model_id].append((now, tokens_used))
        self._model_tokens_day[model_id].append((now, tokens_used))

        if not settings.is_test or str(self._ledger_path) != str(DEFAULT_QUOTA_LEDGER_PATH):
            self.save_durable_state()

    def inspect_response_headers(
        self,
        provider: str,
        model_id: str,
        headers: dict[str, str] | Any,
        status_code: int = 200,
        response_timestamp: str | None = None,
    ) -> None:
        """Inspects official provider response headers (Groq, Gemini) for rate limits and 429 retries."""
        header_map = {k.lower(): v for k, v in headers.items()} if hasattr(headers, "items") else {}
        now = datetime.now(UTC).timestamp()

        # Capture rate limit header telemetry
        hdrs_to_save = {}
        for key in [
            "x-ratelimit-limit-requests",
            "x-ratelimit-limit-tokens",
            "x-ratelimit-remaining-requests",
            "x-ratelimit-remaining-tokens",
            "x-ratelimit-reset-requests",
            "x-ratelimit-reset-tokens",
            "limit_requests",
            "limit_tokens",
            "remaining_requests",
            "remaining_tokens",
            "reset_requests",
            "reset_tokens",
            "retry-after",
        ]:
            if key in header_map:
                hdrs_to_save[key] = header_map[key]

        if hdrs_to_save:
            self._last_provider_headers[model_id] = {
                "headers": hdrs_to_save,
                "response_timestamp": response_timestamp or datetime.now(UTC).isoformat(),
                "recorded_at": now,
            }
            if not settings.is_test or str(self._ledger_path) != str(DEFAULT_QUOTA_LEDGER_PATH):
                self.save_durable_state()

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


governor = CapacityGovernor()
capacity_governor = governor

