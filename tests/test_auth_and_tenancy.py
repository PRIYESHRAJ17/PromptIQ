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
        json={"email": "developer@example.com", "password": "SecurePassword123!", "full_name": "Dev User"},
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
