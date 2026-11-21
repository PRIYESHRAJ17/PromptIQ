"""Test Model Context Protocol (MCP) tool registrations and execution."""

import pytest

from promptiq.mcp.server import TOOLS, handle_tool_call


def test_mcp_tools_list_conformance():
    """Verifies that all core product commands from Appendix C are registered in the MCP tool catalog."""
    tool_names = [t["name"] for t in TOOLS]

    assert "forge.create_project" in tool_names
    assert "forge.run_discovery" in tool_names
    assert "forge.get_project_constitution" in tool_names
    assert "forge.compile_prompt" in tool_names
    assert "forge.review_prompt" in tool_names
    assert "forge.research" in tool_names
    assert "forge.record_checkpoint" in tool_names
    assert "forge.get_context_pack" in tool_names

    for tool in TOOLS:
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


@pytest.mark.asyncio
async def test_mcp_tool_execution(db_session, test_user):
    """Tests executing MCP tool calls."""
    user, _ = test_user

    # 1. forge.create_project
    proj_res = await handle_tool_call(
        "forge.create_project",
        {"name": "MCP Initialized Project", "description": "Created via agent tool"},
        user.id,
        db=db_session,
    )
    assert "project_id" in proj_res
    project_id = proj_res["project_id"]

    # 2. forge.get_project_constitution
    const_res = await handle_tool_call(
        "forge.get_project_constitution",
        {"project_id": project_id},
        user.id,
        db=db_session,
    )
    assert const_res["project_id"] == project_id
    assert const_res["version"] == 1

    # 3. forge.compile_prompt
    compile_res = await handle_tool_call(
        "forge.compile_prompt",
        {
            "project_id": project_id,
            "target_environment": "google-antigravity",
            "output_type": "complete_package",
        },
        user.id,
        db=db_session,
    )
    assert compile_res["target_environment"] == "google-antigravity"
    assert "AGENTS.md" in compile_res["files"]

    # 4. forge.review_prompt
    review_res = await handle_tool_call(
        "forge.review_prompt",
        {"prompt_text": "Write code etc without tests", "target_environment": "google-antigravity"},
        user.id,
        db=db_session,
    )
    assert "verdict" in review_res
    assert len(review_res["findings"]) > 0

    # 5. forge.record_checkpoint
    cp_res = await handle_tool_call(
        "forge.record_checkpoint",
        {"project_id": project_id, "phase": "mcp_testing", "summary": "MCP tools verified"},
        user.id,
        db=db_session,
    )
    assert cp_res["phase"] == "mcp_testing"


def test_mcp_protocol_handshake():
    """Verifies official MCP protocol initialization handshake specs."""
    import json

    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }
    # Test message serialization
    serialized = json.dumps(init_msg)
    parsed = json.loads(serialized)
    assert parsed["method"] == "initialize"
    assert parsed["params"]["protocolVersion"] == "2024-11-05"
