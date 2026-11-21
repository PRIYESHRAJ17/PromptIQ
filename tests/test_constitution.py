"""Test Project Constitution canonical store, provenance, version diffs, and approval gates."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_constitution_lifecycle_versioning_and_approval(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Verifies that Constitution updates create immutable versions, diffs, and require approvals."""
    # 1. Create Project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Constitution Test Project", "description": "Baseline specification"},
        headers=user_auth_headers,
    )
    project_id = proj_resp.json()["id"]

    # 2. Get active initial Constitution (version 1, unapproved)
    const_resp = await client.get(f"/api/v1/projects/{project_id}/constitution", headers=user_auth_headers)
    assert const_resp.status_code == 200
    const_data = const_resp.json()
    assert const_data["version"] == 1
    assert const_data["is_approved"] is False

    # 3. Attempting to compile without user approval MUST fail with 422
    compile_fail = await client.post(
        f"/api/v1/projects/{project_id}/compile",
        json={"target_environment": "google-antigravity", "output_type": "complete_package"},
        headers=user_auth_headers,
    )
    assert compile_fail.status_code == 422
    assert "not approved" in compile_fail.json()["detail"].lower()

    # 4. Update Constitution with verified requirements and provenance
    update_payload = {
        "goals": ["Build secure incident orchestrator"],
        "requirements": [
            {
                "id": "REQ-AUTH-001",
                "text": "System must enforce OAuth2 and role-based permissions.",
                "category": "security",
                "priority": "P0",
                "status": "confirmed",
                "provenance": "user_provided",
                "acceptance_criteria": "Unauthorized requests return HTTP 401/403",
            },
            {
                "id": "REQ-INF-002",
                "text": "System must expose OpenAPI documentation.",
                "category": "functional",
                "priority": "P1",
                "status": "confirmed",
                "provenance": "inferred",
                "acceptance_criteria": "/docs and /openapi.json are accessible",
            },
        ],
        "scope_in": ["Incident API", "CLI"],
        "scope_out": ["Website Frontend"],
    }
    update_resp = await client.put(
        f"/api/v1/projects/{project_id}/constitution",
        json=update_payload,
        headers=user_auth_headers,
    )
    assert update_resp.status_code == 200
    v2_data = update_resp.json()

    # Verify version advanced to 2
    assert v2_data["version"] == 2
    assert v2_data["is_approved"] is False
    assert len(v2_data["requirements"]) == 2
    assert v2_data["requirements"][0]["provenance"] == "user_provided"
    assert v2_data["requirements"][1]["provenance"] == "inferred"

    # Verify immutable snapshot of Version 1 is preserved
    v1_hist = await client.get(f"/api/v1/projects/{project_id}/constitution/versions/1", headers=user_auth_headers)
    assert v1_hist.status_code == 200
    assert v1_hist.json()["version"] == 1

    # 5. User approves Constitution v2
    approve_resp = await client.post(
        f"/api/v1/projects/{project_id}/constitution/approve",
        json={"approve": True, "feedback": "Approved for compilation"},
        headers=user_auth_headers,
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["is_approved"] is True

    # 6. Now compilation MUST succeed!
    compile_success = await client.post(
        f"/api/v1/projects/{project_id}/compile",
        json={"target_environment": "google-antigravity", "output_type": "complete_package"},
        headers=user_auth_headers,
    )
    assert compile_success.status_code == 201
    pkg = compile_success.json()
    assert pkg["target_environment"] == "google-antigravity"
    assert "plugin.json" in pkg["files"]
    assert "AGENTS.md" in pkg["files"]
