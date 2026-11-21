"""Model Context Protocol (MCP) JSON-RPC standard server for PromptIQ."""

import asyncio
import json
import sys
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.compiler.target_compiler import target_compiler
from promptiq.core.database import async_session_factory, init_db
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.discovery.adaptive import AdaptiveDiscoveryEngine
from promptiq.memory.checkpoint import CheckpointManager
from promptiq.memory.context_compiler import ContextCompiler
from promptiq.research.engine import research_engine
from promptiq.schemas.constitution import (
    ConstitutionApprovalRequest,
)
from promptiq.schemas.critic import AutopsyRequest
from promptiq.schemas.discovery import InitialIntakeRequest
from promptiq.schemas.memory import CheckpointCreate, ContextPackRequest
from promptiq.schemas.project import ProjectCreate
from promptiq.schemas.research import ResearchRequest
from promptiq.services.auth_service import AuthService
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService

TOOLS = [
    {
        "name": "forge.create_project",
        "description": "Create a new PromptIQ project with an initial Project Constitution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Project goal or problem statement"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "forge.run_discovery",
        "description": "Start or continue adaptive discovery for a project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "goal": {"type": "string"},
                "depth": {"type": "string", "enum": ["quick", "guided", "deep"]},
            },
            "required": ["project_id", "goal"],
        },
    },
    {
        "name": "forge.get_project_constitution",
        "description": "Retrieve the canonical Project Constitution source of truth.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "forge.compile_prompt",
        "description": "Compile the approved Constitution into target-native instructions (Antigravity, Claude Code, Cursor, Codex).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "target_environment": {"type": "string", "default": "google-antigravity"},
                "output_type": {"type": "string", "enum": ["prompt_only", "prompt_suite", "complete_package"], "default": "complete_package"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "forge.review_prompt",
        "description": "Execute adversarial prompt autopsy and diagnostic critique.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt_text": {"type": "string", "description": "Prompt text to diagnose"},
                "target_environment": {"type": "string", "default": "google-antigravity"},
            },
            "required": ["prompt_text"],
        },
    },
    {
        "name": "forge.research",
        "description": "Investigate technical documentation and record claims in the Evidence Ledger.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "query": {"type": "string"},
                "mode": {"type": "string", "enum": ["quick", "decision", "deep"], "default": "quick"},
            },
            "required": ["project_id", "query"],
        },
    },
    {
        "name": "forge.record_checkpoint",
        "description": "Record a verified project milestone checkpoint for cross-agent continuity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "phase": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["project_id", "phase", "summary"],
        },
    },
    {
        "name": "forge.get_context_pack",
        "description": "Compile and pack project context for an external agent within a token budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "max_token_budget": {"type": "integer", "default": 8000},
            },
            "required": ["project_id"],
        },
    },
]


async def _dispatch_tool(db: AsyncSession, tool_name: str, arguments: dict[str, Any], user_id: str) -> dict[str, Any]:
    if tool_name == "forge.create_project":
        project = await ProjectService.create_project(
            db, user_id, ProjectCreate(name=arguments["name"], description=arguments.get("description")), surface="mcp"
        )
        return {"project_id": project.id, "name": project.name, "version": project.current_constitution_version}

    elif tool_name == "forge.run_discovery":
        intake = InitialIntakeRequest(
            goal=arguments["goal"],
            depth=arguments.get("depth", "guided"),
        )
        res = await AdaptiveDiscoveryEngine.start_session(db, arguments["project_id"], user_id, intake)
        return res.model_dump()

    elif tool_name == "forge.get_project_constitution":
        constitution = await ConstitutionService.get_current_constitution(db, arguments["project_id"], user_id)
        return {
            "project_id": constitution.project_id,
            "version": constitution.version,
            "is_approved": constitution.is_approved,
            "goals": constitution.goals,
            "requirements": constitution.requirements,
            "scope": constitution.scope,
            "technical_direction": constitution.technical_direction,
        }

    elif tool_name == "forge.compile_prompt":
        # Auto-approve for MCP direct compilation convenience if unapproved
        constitution = await ConstitutionService.get_current_constitution(db, arguments["project_id"], user_id)
        if not constitution.is_approved:
            await ConstitutionService.approve_constitution(
                db, arguments["project_id"], user_id, ConstitutionApprovalRequest(approve=True), surface="mcp"
            )

        pkg = await target_compiler.compile_package(
            db,
            arguments["project_id"],
            user_id,
            target_environment=arguments.get("target_environment", "google-antigravity"),
            output_type=arguments.get("output_type", "complete_package"),
            surface="mcp",
        )
        return pkg.model_dump()

    elif tool_name == "forge.review_prompt":
        autopsy_req = AutopsyRequest(
            prompt_text=arguments["prompt_text"],
            target_environment=arguments.get("target_environment", "google-antigravity"),
        )
        res = await PromptAutopsyEngine.diagnose_prompt(autopsy_req, user_id=user_id)
        return res.model_dump()

    elif tool_name == "forge.research":
        req = ResearchRequest(query=arguments["query"], mode=arguments.get("mode", "quick"))
        res = await research_engine.execute_research(db, arguments["project_id"], user_id, req)
        return res.model_dump()

    elif tool_name == "forge.record_checkpoint":
        cp_in = CheckpointCreate(phase=arguments["phase"], summary=arguments["summary"])
        res = await CheckpointManager.create_checkpoint(db, arguments["project_id"], user_id, cp_in, surface="mcp")
        return res.model_dump()

    elif tool_name == "forge.get_context_pack":
        req = ContextPackRequest(max_token_budget=arguments.get("max_token_budget", 8000))
        res = await ContextCompiler.compile_context(db, arguments["project_id"], user_id, req)
        return res.model_dump()

    else:
        raise ValueError(f"Unknown MCP tool '{tool_name}'")


async def handle_tool_call(tool_name: str, arguments: dict[str, Any], user_id: str, db: AsyncSession | None = None) -> dict[str, Any]:
    """Routes an MCP tool call to the corresponding PromptIQ service."""
    if db is not None:
        return await _dispatch_tool(db, tool_name, arguments, user_id)

    async with async_session_factory() as session:
        result = await _dispatch_tool(session, tool_name, arguments, user_id)
        await session.commit()
        return result


async def run_stdio_mcp_server():
    """Runs standard stdio MCP JSON-RPC protocol loop."""
    await init_db()

    # Create/resolve default MCP user
    async with async_session_factory() as db:
        user = await AuthService.get_user_by_telegram_id(db, "mcp_host")
        if not user:
            from promptiq.schemas.auth import UserCreate
            user, _ = await AuthService.register_user(
                db, UserCreate(email="mcp_agent@promptiq.local", password="mcp_password_12345", full_name="MCP Agent")
            )
            await AuthService.link_telegram_account(db, user.id, "mcp_host")
        mcp_user_id = user.id

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break

        line_str = line.decode("utf-8").strip()
        if not line_str:
            continue

        try:
            rpc_req = json.loads(line_str)
            req_id = rpc_req.get("id")
            method = rpc_req.get("method")
            params = rpc_req.get("params", {})

            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS},
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result_data = await handle_tool_call(tool_name, arguments, mcp_user_id)
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result_data, indent=2)}]
                    },
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {},
                }

            out_bytes = (json.dumps(response) + "\n").encode("utf-8")
            sys.stdout.buffer.write(out_bytes)
            sys.stdout.buffer.flush()

        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)},
            }
            sys.stdout.buffer.write((json.dumps(err_resp) + "\n").encode("utf-8"))
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    asyncio.run(run_stdio_mcp_server())
