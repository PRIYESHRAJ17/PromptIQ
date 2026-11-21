"""Test Authentication, Multi-Tenancy, and Tenant Isolation."""

import pytest
from httpx import AsyncClient

from promptiq.core.exceptions import AuthenticationError
from promptiq.core.security import generate_telegram_link_token, verify_telegram_link_token


@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    """Tests standard registration, token issuance, and login."""
    # Register
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "developer@example.com",
            "password": "SecurePassword123!",
            "full_name": "Dev User",
        },
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "developer@example.com"

    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "developer@example.com", "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    client: AsyncClient,
    user_auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
):
    """
    REQ-SEC-001 Invariant Assertion:
    User A in Workspace A creates a project.
    User B in Workspace B MUST NOT be able to view, edit, or delete User A's project.
    """
    # User A creates a project
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Alice Confidential Core", "description": "Proprietary design"},
        headers=user_auth_headers,
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    # User A can access it
    alice_get = await client.get(f"/api/v1/projects/{project_id}", headers=user_auth_headers)
    assert alice_get.status_code == 200

    # User B attempts to access User A's project -> MUST BE FORBIDDEN (403)
    bob_get = await client.get(f"/api/v1/projects/{project_id}", headers=second_auth_headers)
    assert bob_get.status_code in (403, 404)

    # User B attempts to delete User A's project -> MUST BE FORBIDDEN (403)
    bob_delete = await client.delete(f"/api/v1/projects/{project_id}", headers=second_auth_headers)
    assert bob_delete.status_code in (403, 404)

    # Confirm project still exists for User A
    alice_check = await client.get(f"/api/v1/projects/{project_id}", headers=user_auth_headers)
    assert alice_check.status_code == 200


@pytest.mark.asyncio
async def test_telegram_link_token_lifecycle():
    """Tests generation and verification of signed Telegram linking HMAC tokens."""
    user_id = "test-user-uuid-12345"
    token = generate_telegram_link_token(user_id, expires_in_minutes=10)

    # Valid token verification
    verified_id = verify_telegram_link_token(token)
    assert verified_id == user_id

    # Tampered token verification fails
    tampered_token = token[:-5] + "abcde"
    with pytest.raises(AuthenticationError):
        verify_telegram_link_token(tampered_token)

    # Expired token verification fails
    expired_token = generate_telegram_link_token(user_id, expires_in_minutes=-1)
    with pytest.raises(AuthenticationError):
        verify_telegram_link_token(expired_token)


@pytest.mark.asyncio
async def test_telegram_link_api_endpoint(client: AsyncClient, test_user):
    """Tests the /api/v1/auth/telegram-link API route with token verification."""
    user, _ = test_user
    link_token = generate_telegram_link_token(user.id, expires_in_minutes=15)

    # Valid link request
    resp = await client.post(
        "/api/v1/auth/telegram-link",
        json={"telegram_chat_id": "9988776655", "link_token": link_token},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Invalid/tampered link token MUST be rejected
    fail_resp = await client.post(
        "/api/v1/auth/telegram-link",
        json={"telegram_chat_id": "11223344", "link_token": "invalid:token:signature"},
    )
    assert fail_resp.status_code == 401


@pytest.mark.asyncio
async def test_exhaustive_cross_tenant_idor_enforcement(
    client: AsyncClient,
    user_auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
):
    """
    Exhaustive Adversarial IDOR Audit:
    User A creates a project. User B attempts unauthorized access, mutation,
    or execution across EVERY project-scoped endpoint. All MUST return 403 or 404.
    """
    # 1. User A creates project and compiles a package
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Alice Private Project", "description": "Highly confidential"},
        headers=user_auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # User A approves constitution and compiles
    await client.post(
        f"/api/v1/projects/{project_id}/constitution/approve",
        json={"approve": True},
        headers=user_auth_headers,
    )
    pkg_resp = await client.post(
        f"/api/v1/projects/{project_id}/compile",
        json={"target_environment": "google-antigravity", "output_type": "complete_package"},
        headers=user_auth_headers,
    )
    assert pkg_resp.status_code == 201
    package_id = pkg_resp.json()["id"]

    # 2. User B attacks Constitution
    # GET Constitution
    b_const_get = await client.get(
        f"/api/v1/projects/{project_id}/constitution", headers=second_auth_headers
    )
    assert b_const_get.status_code in (403, 404)

    # PUT Constitution update
    b_const_put = await client.put(
        f"/api/v1/projects/{project_id}/constitution",
        json={"goals": ["Malicious takeover"]},
        headers=second_auth_headers,
    )
    assert b_const_put.status_code in (403, 404)

    # POST Constitution approve
    b_const_app = await client.post(
        f"/api/v1/projects/{project_id}/constitution/approve",
        json={"approve": True},
        headers=second_auth_headers,
    )
    assert b_const_app.status_code in (403, 404)

    # GET Constitution historical snapshot
    b_const_snap = await client.get(
        f"/api/v1/projects/{project_id}/constitution/versions/1", headers=second_auth_headers
    )
    assert b_const_snap.status_code in (403, 404)

    # 3. User B attacks Discovery
    # POST Discovery start
    b_disc_start = await client.post(
        f"/api/v1/projects/{project_id}/discovery/start",
        json={
            "goal": "Infiltrate",
            "deliverable": "complete_package",
            "target": "google-antigravity",
            "depth": "quick",
        },
        headers=second_auth_headers,
    )
    assert b_disc_start.status_code in (403, 404)

    # 4. User B attacks Compiler & Package Export
    # POST Compile
    b_compile = await client.post(
        f"/api/v1/projects/{project_id}/compile",
        json={"target_environment": "google-antigravity", "output_type": "complete_package"},
        headers=second_auth_headers,
    )
    assert b_compile.status_code in (403, 404)

    # GET Package Export
    b_export = await client.get(
        f"/api/v1/projects/{project_id}/packages/{package_id}/export", headers=second_auth_headers
    )
    assert b_export.status_code in (403, 404)

    # 5. User B attacks Project Memory & Checkpoints
    # POST Checkpoint create
    b_cp_create = await client.post(
        f"/api/v1/projects/{project_id}/memory/checkpoints",
        json={"phase": "compromised", "summary": "fake summary"},
        headers=second_auth_headers,
    )
    assert b_cp_create.status_code in (403, 404)

    # GET Checkpoints list
    b_cp_list = await client.get(
        f"/api/v1/projects/{project_id}/memory/checkpoints", headers=second_auth_headers
    )
    assert b_cp_list.status_code in (403, 404)

    # POST Context pack
    b_ctx_pack = await client.post(
        f"/api/v1/projects/{project_id}/memory/context-pack",
        json={"target_environment": "google-antigravity", "max_token_budget": 2000},
        headers=second_auth_headers,
    )
    assert b_ctx_pack.status_code in (403, 404)

    # 6. User B attacks Research Engine
    b_research = await client.post(
        f"/api/v1/projects/{project_id}/research",
        json={"query": "Exfiltrate user data", "mode": "quick"},
        headers=second_auth_headers,
    )
    assert b_research.status_code in (403, 404)

    # 7. User B attacks Evaluation Lab
    b_suite_create = await client.post(
        f"/api/v1/projects/{project_id}/eval/suites",
        json={"name": "Attacker Suite", "description": "unauthorized", "test_cases": []},
        headers=second_auth_headers,
    )
    assert b_suite_create.status_code in (403, 404)

    # 8. User B attempts Prompt Autopsy on User A's package_id
    b_autopsy = await client.post(
        "/api/v1/critic/autopsy",
        json={"package_id": package_id},
        headers=second_auth_headers,
    )
    assert b_autopsy.status_code in (403, 404)
