"""Comprehensive regression tests for authentication hardening, token revocation, and session rotation."""

import pytest
from httpx import AsyncClient


async def _register_user(client: AsyncClient, email: str = "session_test@promptiq.dev", password: str = "StrongPassword123!"):
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Session Tester",
        },
    )
    assert res.status_code == 201
    return res.json()


@pytest.mark.asyncio
async def test_register_and_login_return_refresh_token(client: AsyncClient):
    """Verifies that both register and login issue valid access and refresh tokens."""
    reg_data = await _register_user(client, "reg_test@promptiq.dev")
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["refresh_token"] is not None

    # Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "reg_test@promptiq.dev",
            "password": "StrongPassword123!",
        },
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["refresh_token"] is not None


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_replay_protection(client: AsyncClient):
    """Verifies that refreshing rotates the refresh token and replaying an old refresh token is rejected."""
    reg_data = await _register_user(client, "rotate_test@promptiq.dev")
    refresh_1 = reg_data["refresh_token"]

    # First refresh -> should succeed and issue new refresh token
    ref_res_1 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_1},
    )
    assert ref_res_1.status_code == 200
    ref_data_1 = ref_res_1.json()
    refresh_2 = ref_data_1["refresh_token"]
    assert refresh_2 != refresh_1

    # Replay old refresh token -> must be rejected
    ref_res_replay = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_1},
    )
    assert ref_res_replay.status_code == 401
    assert "already been used" in ref_res_replay.json()["detail"]

    # Use new refresh token -> should succeed
    ref_res_2 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_2},
    )
    assert ref_res_2.status_code == 200
    refresh_3 = ref_res_2.json()["refresh_token"]
    assert refresh_3 != refresh_2


@pytest.mark.asyncio
async def test_logout_revokes_access_token(client: AsyncClient):
    """Verifies that logout revokes access token so subsequent authenticated requests fail."""
    reg_data = await _register_user(client, "logout_test@promptiq.dev")
    access_token = reg_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Profile check before logout -> 200 OK
    me_before = await client.get("/api/v1/auth/me", headers=headers)
    assert me_before.status_code == 200

    # Logout
    logout_res = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Profile check after logout -> 401 Unauthorized (revoked)
    me_after = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401
    assert "revoked" in me_after.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_invalidates_refresh_sessions(client: AsyncClient):
    """Verifies that changing password updates password and revokes previous refresh tokens."""
    reg_data = await _register_user(client, "pw_test@promptiq.dev")
    access_token = reg_data["access_token"]
    old_refresh = reg_data["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Change password
    cp_res = await client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={
            "current_password": "StrongPassword123!",
            "new_password": "BrandNewPassword999!",
        },
    )
    assert cp_res.status_code == 200

    # Attempt to refresh with old refresh token -> must fail
    ref_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert ref_res.status_code == 401

    # Login with old password -> must fail
    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "pw_test@promptiq.dev",
            "password": "StrongPassword123!",
        },
    )
    assert old_login.status_code == 401

    # Login with new password -> must succeed
    new_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "pw_test@promptiq.dev",
            "password": "BrandNewPassword999!",
        },
    )
    assert new_login.status_code == 200
