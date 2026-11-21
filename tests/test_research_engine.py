"""Test Research Intelligence Engine and Evidence Ledger."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_research_investigation_and_evidence_ledger(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Verifies that research populates the Evidence Ledger with dated primary sources and locators."""
    # 1. Create a project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Research Test Project"},
        headers=user_auth_headers,
    )
    project_id = proj_resp.json()["id"]

    # 2. Execute Research
    research_payload = {
        "query": "Model Context Protocol tools and standard transports",
        "mode": "deep",
        "max_sources": 3,
    }
    res_resp = await client.post(
        f"/api/v1/projects/{project_id}/research",
        json=research_payload,
        headers=user_auth_headers,
    )
    assert res_resp.status_code == 201
    data = res_resp.json()

    assert data["status"] == "completed"
    assert len(data["sources"]) > 0
    assert len(data["claims"]) > 0

    # Verify source metadata
    source = data["sources"][0]
    assert source["url"].startswith("http")
    assert len(source["publisher"]) > 0
    assert source["retrieved_at"] is not None

    # Verify Evidence Ledger claim
    claim = data["claims"][0]
    assert len(claim["claim_text"]) > 0
    assert claim["support_status"] == "verified"
    assert claim["confidence_score"] > 0.8
    assert len(claim["confidence_rationale"]) > 0


@pytest.mark.asyncio
async def test_live_web_search_connector():
    """Verifies LiveWebSearchConnector with graceful fallback handling."""
    from promptiq.research.connectors.live_search import LiveWebSearchConnector

    connector = LiveWebSearchConnector(fallback_on_error=True)
    results = await connector.search("FastAPI", max_results=2)
    assert len(results) > 0
    assert "url" in results[0]
    assert "publisher" in results[0]

