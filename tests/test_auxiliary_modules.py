"""Tests for auxiliary modules: Metrics, Specialist Orchestrator, Client Bridge, and SDK Client."""

import pytest
from httpx import ASGITransport, AsyncClient

from promptiq.api.main import app
from promptiq.mcp.client_bridge import run_bridge
from promptiq.observability.metrics import MetricsCollector
from promptiq.orchestrator.task_graph import SpecialistOrchestrator
from promptiq.sdk.client import PromptIQClient


def test_metrics_collector():
    collector = MetricsCollector()
    collector.record_request("/health", 200, 12.5)
    collector.record_request("/health", 200, 15.5)
    collector.record_request("/api/v1/projects", 500, 120.0)
    collector.record_tokens(1500)
    collector.record_circuit_trip()

    summary = collector.get_summary()
    assert summary["total_requests"] == 3
    assert summary["requests_by_endpoint"]["/health"] == 2
    assert summary["errors_by_endpoint"]["/api/v1/projects"] == 1
    assert summary["average_latency_ms"]["/health"] == 14.0
    assert summary["tokens_estimated"] == 1500
    assert summary["circuit_breaker_trips"] == 1


@pytest.mark.asyncio
async def test_specialist_orchestrator():
    res = await SpecialistOrchestrator.run_pipeline(
        task_name="test_pipeline",
        input_context="Build a robust CLI",
        user_id="test_user",
        specialists=["prompt_architect"],
        max_steps=1,
    )
    assert res["task_name"] == "test_pipeline"
    assert res["steps_completed"] == 1
    assert "prompt_architect" in res["specialist_outputs"]
    assert res["status"] == "completed"


def test_client_bridge_scheme_validation():
    with pytest.raises(ValueError) as exc_info:
        run_bridge("file:///etc/passwd")
    assert "Invalid scheme" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        run_bridge("ftp://malicious.com")
    assert "Invalid scheme" in str(exc_info.value)


@pytest.mark.asyncio
async def test_sdk_client_integration():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        sdk = PromptIQClient(base_url="http://test")
        sdk._client = ac

        # Test health endpoint through underlying client
        resp = await sdk._client.get("/health")
        assert resp.status_code == 200

        # Test auth headers helper
        assert sdk._headers() == {"Content-Type": "application/json"}
        sdk.token = "fake-token-xyz"
        assert sdk._headers() == {
            "Content-Type": "application/json",
            "Authorization": "Bearer fake-token-xyz",
        }
