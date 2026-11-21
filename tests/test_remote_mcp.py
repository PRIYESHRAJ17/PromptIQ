"""Test Remote Model Context Protocol (MCP) HTTP / SSE and Readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """Verifies the /ready endpoint checks database readiness."""
    resp = await client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_remote_mcp_stateless_rpc(client: AsyncClient, user_auth_headers: dict[str, str]):
    """Verifies the /api/v1/mcp/rpc stateless JSON-RPC endpoint for remote agents."""
    # 1. initialize method
    init_payload = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    init_resp = await client.post("/api/v1/mcp/rpc", json=init_payload, headers=user_auth_headers)
    assert init_resp.status_code == 200
    data = init_resp.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 101
    assert data["result"]["serverInfo"]["name"] == "promptiq-cloud-mcp"

    # 2. tools/list method
    tools_payload = {
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/list",
        "params": {},
    }
    tools_resp = await client.post("/api/v1/mcp/rpc", json=tools_payload, headers=user_auth_headers)
    assert tools_resp.status_code == 200
    tools_data = tools_resp.json()
    assert len(tools_data["result"]["tools"]) >= 8

    # 3. tools/call create_project method
    call_payload = {
        "jsonrpc": "2.0",
        "id": 103,
        "method": "tools/call",
        "params": {
            "name": "forge.create_project",
            "arguments": {"name": "Remote MCP Project", "description": "Cloud initiated"},
        },
    }
    call_resp = await client.post("/api/v1/mcp/rpc", json=call_payload, headers=user_auth_headers)
    assert call_resp.status_code == 200
    call_data = call_resp.json()
    assert "result" in call_data
    assert "content" in call_data["result"]
    assert "project_id" in call_data["result"]["content"][0]["text"]

    # 4. method not found returns code -32601
    unknown_payload = {
        "jsonrpc": "2.0",
        "id": 104,
        "method": "non_existent_tool_action",
    }
    unknown_resp = await client.post(
        "/api/v1/mcp/rpc", json=unknown_payload, headers=user_auth_headers
    )
    assert unknown_resp.status_code == 200
    unknown_data = unknown_resp.json()
    assert unknown_data["error"]["code"] == -32601


@pytest.mark.asyncio
async def test_remote_mcp_sse_cross_tenant_isolation(
    client: AsyncClient,
    user_auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
):
    """Verifies that an authenticated tenant cannot inject messages into another tenant's SSE session."""
    import asyncio

    from promptiq.mcp.remote import _active_sse_sessions

    # Simulate an active SSE session belonging to tenant A (from user_auth_headers)
    fake_session_id = "tenant-a-active-session-id"
    tenant_a_queue = asyncio.Queue()
    # Resolve tenant A user id from an authenticated call
    me_resp = await client.get("/api/v1/projects", headers=user_auth_headers)
    assert me_resp.status_code == 200

    # Inject session bound to tenant A
    _active_sse_sessions[fake_session_id] = {
        "queue": tenant_a_queue,
        "user_id": "tenant-a-user-id",
    }

    try:
        # Tenant B tries to post into Tenant A's session
        hijack_payload = {
            "jsonrpc": "2.0",
            "id": 999,
            "method": "ping",
        }
        hijack_resp = await client.post(
            f"/api/v1/mcp/messages?sessionId={fake_session_id}",
            json=hijack_payload,
            headers=second_auth_headers,
        )
        assert hijack_resp.status_code == 403
        assert "another tenant" in hijack_resp.json()["detail"].lower()
    finally:
        _active_sse_sessions.pop(fake_session_id, None)


@pytest.mark.asyncio
async def test_streamable_http_primary_transport(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Verifies official MCP Streamable HTTP primary transport on /api/v1/mcp."""
    # 1. Standard application/json response
    init_payload = {
        "jsonrpc": "2.0",
        "id": 201,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    resp = await client.post(
        "/api/v1/mcp",
        json=init_payload,
        headers={**user_auth_headers, "Accept": "application/json"},
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    assert resp.json()["result"]["serverInfo"]["name"] == "promptiq-cloud-mcp"

    # 2. text/event-stream chunked SSE response over HTTP POST
    sse_req_payload = {
        "jsonrpc": "2.0",
        "id": 202,
        "method": "ping",
    }
    sse_resp = await client.post(
        "/api/v1/mcp",
        json=sse_req_payload,
        headers={**user_auth_headers, "Accept": "text/event-stream"},
    )
    assert sse_resp.status_code == 200
    assert "text/event-stream" in sse_resp.headers["content-type"]
    body = sse_resp.text
    assert "event: message" in body
    assert '"id": 202' in body


@pytest.mark.asyncio
async def test_streamable_http_origin_security(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Verifies Origin header validation prevents DNS rebinding attacks."""
    ping_payload = {"jsonrpc": "2.0", "id": 203, "method": "ping"}

    # Suspicious origin MUST be rejected with 403 Forbidden
    bad_resp = await client.post(
        "/api/v1/mcp",
        json=ping_payload,
        headers={**user_auth_headers, "Origin": "http://evil-attacker-site.com"},
    )
    assert bad_resp.status_code == 403
    assert "rebinding" in bad_resp.json()["detail"].lower()

    # Allowed localhost origin passes
    good_resp = await client.post(
        "/api/v1/mcp",
        json=ping_payload,
        headers={**user_auth_headers, "Origin": "http://localhost:3000"},
    )
    assert good_resp.status_code == 200
