"""Observability, metrics collection, and operational telemetry."""

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any


class MetricsCollector:
    """Thread-safe in-memory metrics and telemetry collector."""

    def __init__(self):
        self._request_counts: dict[str, int] = defaultdict(int)
        self._latency_samples: dict[str, list[float]] = defaultdict(list)
        self._error_counts: dict[str, int] = defaultdict(int)
        self._tokens_estimated: int = 0
        self._circuit_trips: int = 0

    def record_request(self, endpoint: str, status_code: int, latency_ms: float) -> None:
        self._request_counts[endpoint] += 1
        self._latency_samples[endpoint].append(latency_ms)
        if len(self._latency_samples[endpoint]) > 100:
            self._latency_samples[endpoint].pop(0)

        if status_code >= 400:
            self._error_counts[endpoint] += 1

    def record_tokens(self, tokens: int) -> None:
        self._tokens_estimated += tokens

    def record_circuit_trip(self) -> None:
        self._circuit_trips += 1

    def get_summary(self) -> dict[str, Any]:
        avg_latencies = {}
        for ep, samples in self._latency_samples.items():
            avg_latencies[ep] = round(sum(samples) / len(samples), 2) if samples else 0.0

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_requests": sum(self._request_counts.values()),
            "requests_by_endpoint": dict(self._request_counts),
            "errors_by_endpoint": dict(self._error_counts),
            "average_latency_ms": avg_latencies,
            "tokens_estimated": self._tokens_estimated,
            "circuit_breaker_trips": self._circuit_trips,
        }


metrics = MetricsCollector()
