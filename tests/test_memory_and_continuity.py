"""Test Project Memory, Checkpointing, and Context Continuity."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_context_compiler_and_checkpointing(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Verifies that Context Compiler packs memory within token limits and tracks checkpoints."""
    # 1. Create Project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Continuity Test Project", "description": "Persistent memory validation"},
        headers=user_auth_headers,
    )
    project_id = proj_resp.json()["id"]

    # 2. Record a verified milestone Checkpoint
    cp_payload = {
        "phase": "architecture_aligned",
        "summary": "Modular monolith boundaries and data models established.",
        "verified_state": {"tables_created": 15, "auth_enabled": True},
        "blockers": [],
        "next_actions": ["Implement adapter compilers", "Run automated test suite"],
    }
    cp_resp = await client.post(
        f"/api/v1/projects/{project_id}/memory/checkpoints",
        json=cp_payload,
        headers=user_auth_headers,
    )
    assert cp_resp.status_code == 201
    cp_data = cp_resp.json()
    assert cp_data["phase"] == "architecture_aligned"

    # Verify list checkpoints
    list_resp = await client.get(
        f"/api/v1/projects/{project_id}/memory/checkpoints",
        headers=user_auth_headers,
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 3. Test Context Compiler packaging
    pack_payload = {
        "target_environment": "google-antigravity",
        "max_token_budget": 4000,
        "include_research": True,
    }
    pack_resp = await client.post(
        f"/api/v1/projects/{project_id}/memory/context-pack",
        json=pack_payload,
        headers=user_auth_headers,
    )
    assert pack_resp.status_code == 200
    pack_data = pack_resp.json()

    assert pack_data["project_id"] == project_id
    assert pack_data["estimated_tokens"] <= 4000
    assert "goals" in pack_data["items_included"]
    assert "# PROJECT CONTEXT" in pack_data["packed_context_markdown"]
