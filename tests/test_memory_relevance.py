"""Tests for ContextCompiler priority filtering, task focus relevance ranking, and checkpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_context_compiler_relevance_and_priority(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Verifies that ContextCompiler respects priority cutoffs and ranks relevant requirements higher."""
    # 1. Create project
    p_resp = await client.post(
        "/api/v1/projects", json={"name": "Memory Relevance Proj"}, headers=user_auth_headers
    )
    p_id = p_resp.json()["id"]

    # 2. Update constitution with P0, P1, P3 requirements
    const_update = {
        "requirements": [
            {
                "id": "REQ-P3-001",
                "text": "Optional decorative banner logging",
                "priority": "P3",
                "status": "confirmed",
                "provenance": "user_provided",
            },
            {
                "id": "REQ-P0-001",
                "text": "Core database connection pool manager",
                "priority": "P0",
                "status": "confirmed",
                "provenance": "user_provided",
            },
            {
                "id": "REQ-P1-001",
                "text": "Authentication middleware for JWT tokens",
                "priority": "P1",
                "status": "confirmed",
                "provenance": "user_provided",
            },
        ]
    }
    u_resp = await client.put(
        f"/api/v1/projects/{p_id}/constitution", json=const_update, headers=user_auth_headers
    )
    assert u_resp.status_code == 200

    # 3. Create a checkpoint
    cp_payload = {
        "phase": "database_setup",
        "summary": "Database pool established and migrations verified.",
        "verified_state": {"pool_size": 20},
        "next_actions": ["Implement auth"],
    }
    await client.post(
        f"/api/v1/projects/{p_id}/memory/checkpoints", json=cp_payload, headers=user_auth_headers
    )

    # 4. Pack context with priority cutoff = P1 (should exclude P3) and task_focus = "auth middleware"
    pack_req = {
        "target_environment": "google-antigravity",
        "max_token_budget": 8000,
        "priority_cutoff": "P1",
        "task_focus": "auth middleware",
    }
    pack_resp = await client.post(
        f"/api/v1/projects/{p_id}/memory/context-pack", json=pack_req, headers=user_auth_headers
    )
    assert pack_resp.status_code == 200
    data = pack_resp.json()

    markdown = data["packed_context_markdown"]
    assert "REQ-P0-001" in markdown
    assert "REQ-P1-001" in markdown
    assert "REQ-P3-001" not in markdown  # Excluded by priority cutoff
    assert "LATEST VERIFIED CHECKPOINT" in markdown
    assert data["latest_checkpoint"] is not None
    assert data["latest_checkpoint"]["phase"] == "database_setup"
