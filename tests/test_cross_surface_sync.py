"""Test Cross-Surface State Synchronization across Web API, Telegram, and MCP."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.mcp.server import handle_tool_call
from promptiq.telegram.bot import telegram_bot


@pytest.mark.asyncio
async def test_project_started_in_telegram_accessible_in_api(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    user_auth_headers: dict[str, str],
):
    """
    SECTION 5 Invariant:
    A project started in Telegram MUST be accessible through the Web API and Integrations without loss of context.
    """
    user, _ = test_user
    chat_id = "1122334455"
    user.telegram_chat_id = chat_id
    await db_session.flush()

    # 1. Start project in Telegram via /build
    tg_update = {
        "message": {
            "chat": {"id": chat_id},
            "text": "/build Distributed Key-Value Store",
        }
    }
    tg_resp = await telegram_bot.handle_update(db_session, tg_update)
    assert tg_resp["status"] == "processed"

    # 2. Access the same project via REST API
    api_list = await client.get("/api/v1/projects", headers=user_auth_headers)
    assert api_list.status_code == 200
    projects = api_list.json()

    matching_proj = next((p for p in projects if "Distributed Key-Value" in p["name"]), None)
    assert matching_proj is not None
    project_id = matching_proj["id"]

    # 3. Retrieve Constitution via MCP tool
    mcp_const = await handle_tool_call(
        "forge.get_project_constitution", {"project_id": project_id}, user.id, db=db_session
    )
    assert mcp_const["project_id"] == project_id
    assert mcp_const["version"] == 1

    # 4. Compile package via MCP tool
    compile_res = await handle_tool_call(
        "forge.compile_prompt",
        {"project_id": project_id, "target_environment": "google-antigravity", "output_type": "complete_package"},
        user.id,
        db=db_session,
    )
    assert compile_res["target_environment"] == "google-antigravity"

    # 5. Verify the compiled package is now retrievable via REST API
    export_resp = await client.get(
        f"/api/v1/projects/{project_id}/packages/{compile_res['id']}/export",
        headers=user_auth_headers,
    )
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["package_id"] == compile_res["id"]
    assert "AGENTS.md" in export_data["files"]
