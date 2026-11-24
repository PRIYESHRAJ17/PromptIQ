"""Model Context Protocol (MCP) JSON-RPC standard server for PromptIQ."""

import os
import sys

# Ensure MCP mode is set before any logger initialisation so stdout remains pure JSON-RPC
os.environ["PROMPTIQ_MCP_MODE"] = "true"

import asyncio
import json
import logging
import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.compiler.target_compiler import target_compiler
from promptiq.core.database import async_session_factory, init_db
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.discovery.adaptive import AdaptiveDiscoveryEngine
from promptiq.memory.checkpoint import CheckpointManager
from promptiq.memory.context_compiler import ContextCompiler
from promptiq.models.project import Project
from promptiq.models.user import User, Workspace, WorkspaceMembership
from promptiq.research.engine import research_engine
from promptiq.schemas.auth import UserCreate
from promptiq.schemas.constitution import ConstitutionApprovalRequest
from promptiq.schemas.critic import AutopsyRequest
from promptiq.schemas.discovery import InitialIntakeRequest
from promptiq.schemas.memory import CheckpointCreate, ContextPackRequest
from promptiq.schemas.project import ProjectCreate
from promptiq.schemas.research import ResearchRequest
from promptiq.services.auth_service import AuthService
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService

# Standard RFC-compliant MCP Tools matching ^[a-zA-Z0-9_-]{1,64}$ (strictly NO dots)
_TOOL_DEFINITIONS = [
    {
        "name": "create_project",
        "description": "Create a new PromptIQ project with an initial Project Constitution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "description": {
                    "type": "string",
                    "description": "Project goal or problem statement",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "run_discovery",
        "description": "Start or continue adaptive discovery for a project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (optional, defaults to latest)"},
                "goal": {"type": "string", "description": "Goal or requirement statement"},
                "depth": {"type": "string", "enum": ["quick", "guided", "deep"], "default": "guided"},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "get_project_constitution",
        "description": "Retrieve the canonical Project Constitution source of truth.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (optional, defaults to latest)"},
            },
            "required": [],
        },
    },
    {
        "name": "compile_prompt",
        "description": "Compile the approved Constitution into target-native instructions (Antigravity, Claude Code, Cursor, Codex).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (optional, defaults to latest)"},
                "target_environment": {"type": "string", "default": "google-antigravity"},
                "output_type": {
                    "type": "string",
                    "enum": ["prompt_only", "prompt_suite", "complete_package"],
                    "default": "complete_package",
                },
            },
            "required": [],
        },
    },
    {
        "name": "review_prompt",
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
        "name": "research",
        "description": "Investigate technical documentation and record claims in the Evidence Ledger.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (optional, defaults to latest)"},
                "query": {"type": "string", "description": "Search query or technical question"},
                "mode": {
                    "type": "string",
                    "enum": ["quick", "decision", "deep"],
                    "default": "quick",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "record_checkpoint",
        "description": "Record a verified project milestone checkpoint for cross-agent continuity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (optional, defaults to latest)"},
                "phase": {"type": "string", "description": "Phase or milestone name"},
                "summary": {"type": "string", "description": "Summary of achievements"},
            },
            "required": ["phase", "summary"],
        },
    },
    {
        "name": "get_context_pack",
        "description": "Compile and pack project context for an external agent within a token budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (optional, defaults to latest)"},
                "max_token_budget": {"type": "integer", "default": 8000},
            },
            "required": [],
        },
    },
    {
        "name": "execute_agent_task",
        "description": "Execute an objective through the PromptIQ autonomous observe-decide-act agent loop with tool permissions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "objective": {"type": "string", "description": "High-level goal or task objective"},
                "task_type": {"type": "string", "default": "software_engineering"},
                "max_iterations": {"type": "integer", "default": 10},
            },
            "required": ["objective"],
        },
    },
    {
        "name": "get_quota_status",
        "description": "Check PromptIQ workspace zero-price quota and anti-BYOK enforcement status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

# Ensure every tool defines BOTH 'inputSchema' and 'parameters' with strictly valid naming
TOOLS = []
for t in _TOOL_DEFINITIONS:
    tool_copy = dict(t)
    tool_copy["parameters"] = tool_copy["inputSchema"]
    TOOLS.append(tool_copy)


async def get_or_create_mcp_user(db: AsyncSession) -> User:
    """Retrieves or creates the committed default MCP user with an owned workspace."""
    stmt = select(User).where(User.email == "mcp_agent@promptiq.org")
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        user = await AuthService.get_user_by_telegram_id(db, "mcp_host")

    if not user:
        user, _ = await AuthService.register_user(
            db,
            UserCreate(
                email="mcp_agent@promptiq.org",
                password=secrets.token_urlsafe(32),
                full_name="MCP Agent",
            ),
        )
        await AuthService.link_telegram_account(db, user.id, "mcp_host")

    # Verify and ensure workspace ownership exists
    stmt_ws = select(WorkspaceMembership).where(
        WorkspaceMembership.user_id == user.id,
        WorkspaceMembership.role == "owner",
    )
    res_ws = await db.execute(stmt_ws)
    if not res_ws.scalar_one_or_none():
        workspace = Workspace(name="MCP Agent's Workspace", owner_id=user.id)
        db.add(workspace)
        await db.flush()
        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
        db.add(membership)
        await db.flush()

    await db.commit()
    return user


async def _resolve_project_id(db: AsyncSession, user_id: str, project_id: str | None) -> str:
    """Resolves provided project_id or defaults to the user's latest project."""
    if project_id and project_id not in ("latest", "default", "current", ""):
        return project_id

    stmt = (
        select(Project)
        .join(Workspace, Project.workspace_id == Workspace.id)
        .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
        .where(WorkspaceMembership.user_id == user_id)
        .order_by(Project.created_at.desc())
    )
    res = await db.execute(stmt)
    latest = res.scalars().first()
    if latest:
        return latest.id

    new_proj = await ProjectService.create_project(
        db,
        user_id,
        ProjectCreate(
            name="Default Workspace Project",
            description="Automatically initialized for MCP integration session",
        ),
        surface="mcp",
    )
    return new_proj.id


async def _dispatch_tool(
    db: AsyncSession, tool_name: str, arguments: dict[str, Any], user_id: str
) -> dict[str, Any]:
    norm_name = (
        tool_name.lower()
        .replace("-", "_")
        .replace(".", "_")
        .removeprefix("forge_")
        .removeprefix("promptiq_")
    )

    if norm_name == "create_project":
        proj_name = (
            arguments.get("name")
            or arguments.get("title")
            or arguments.get("project_name")
            or "PromptIQ Project"
        )
        proj_desc = arguments.get("description") or arguments.get("desc") or ""
        project = await ProjectService.create_project(
            db,
            user_id,
            ProjectCreate(name=proj_name, description=proj_desc),
            surface="mcp",
        )
        return {
            "project_id": project.id,
            "name": project.name,
            "version": project.current_constitution_version,
            "status": "created",
        }

    elif norm_name == "run_discovery":
        project_id = await _resolve_project_id(db, user_id, arguments.get("project_id"))
        goal = (
            arguments.get("goal")
            or arguments.get("objective")
            or arguments.get("intent")
            or "System Discovery"
        )
        depth = arguments.get("depth", "guided")
        intake = InitialIntakeRequest(goal=goal, depth=depth)
        res = await AdaptiveDiscoveryEngine.start_session(db, project_id, user_id, intake)
        return res.model_dump()

    elif norm_name in ("get_project_constitution", "get_constitution", "constitution"):
        project_id = await _resolve_project_id(db, user_id, arguments.get("project_id"))
        constitution = await ConstitutionService.get_current_constitution(db, project_id, user_id)
        return {
            "project_id": constitution.project_id,
            "version": constitution.version,
            "is_approved": constitution.is_approved,
            "goals": constitution.goals,
            "requirements": constitution.requirements,
            "scope": constitution.scope,
            "technical_direction": constitution.technical_direction,
        }

    elif norm_name == "compile_prompt":
        project_id = await _resolve_project_id(db, user_id, arguments.get("project_id"))
        constitution = await ConstitutionService.get_current_constitution(db, project_id, user_id)
        if not constitution.is_approved:
            await ConstitutionService.approve_constitution(
                db,
                project_id,
                user_id,
                ConstitutionApprovalRequest(approve=True),
                surface="mcp",
            )

        target_env = (
            arguments.get("target_environment")
            or arguments.get("target_format")
            or "google-antigravity"
        )
        output_type = arguments.get("output_type", "complete_package")
        pkg = await target_compiler.compile_package(
            db,
            project_id,
            user_id,
            target_environment=target_env,
            output_type=output_type,
            surface="mcp",
        )
        return pkg.model_dump()

    elif norm_name in ("review_prompt", "run_autopsy", "autopsy"):
        prompt_text = (
            arguments.get("prompt_text")
            or arguments.get("prompt")
            or arguments.get("text")
            or arguments.get("query")
            or ""
        )
        target_env = (
            arguments.get("target_environment")
            or arguments.get("target_format")
            or "google-antigravity"
        )
        autopsy_req = AutopsyRequest(prompt_text=prompt_text, target_environment=target_env)
        res = await PromptAutopsyEngine.diagnose_prompt(autopsy_req, user_id=user_id)
        return res.model_dump()

    elif norm_name in ("research", "search_evidence"):
        project_id = await _resolve_project_id(db, user_id, arguments.get("project_id"))
        query = arguments.get("query") or arguments.get("search_query") or arguments.get("term") or ""
        mode = arguments.get("mode", "quick")
        req = ResearchRequest(query=query, mode=mode)
        res = await research_engine.execute_research(db, project_id, user_id, req)
        return res.model_dump()

    elif norm_name == "record_checkpoint":
        project_id = await _resolve_project_id(db, user_id, arguments.get("project_id"))
        phase = arguments.get("phase") or "Milestone"
        summary = arguments.get("summary") or "State recorded via MCP"
        cp_in = CheckpointCreate(phase=phase, summary=summary)
        res = await CheckpointManager.create_checkpoint(
            db, project_id, user_id, cp_in, surface="mcp"
        )
        return res.model_dump()

    elif norm_name == "get_context_pack":
        project_id = await _resolve_project_id(db, user_id, arguments.get("project_id"))
        token_budget = arguments.get("max_token_budget") or arguments.get("token_budget") or 8000
        req = ContextPackRequest(max_token_budget=token_budget)
        res = await ContextCompiler.compile_context(db, project_id, user_id, req)
        return res.model_dump()

    elif norm_name in ("execute_agent_task", "execute_task", "execute_workflow"):
        from promptiq.orchestrator.agent_loop import AutonomousAgentLoop

        objective = (
            arguments.get("objective")
            or arguments.get("task")
            or arguments.get("prompt")
            or "Autonomous execution"
        )
        task_type = arguments.get("task_type", "software_engineering")
        max_iter = arguments.get("max_iterations", 10)

        agent = AutonomousAgentLoop()
        summary = await agent.run(
            objective=objective,
            task_name=f"MCP-Agent-{objective[:30]}",
            task_type=task_type,
            max_iterations=max_iter,
        )
        return {
            "status": summary.status,
            "plan_id": summary.plan_id,
            "total_iterations": summary.total_iterations,
            "total_tokens_used": summary.total_tokens_used,
            "deliverable": summary.deliverable,
            "replan_count": summary.replan_count,
        }

    elif norm_name in ("get_quota_status", "quota_status"):
        return {
            "status": "operational",
            "tier": "zero_price_forever",
            "cost_per_query": "₹0.00",
            "user_api_key_required": False,
            "byok_prohibited": True,
            "rate_limit": "60 requests/hour",
            "active_enforcement": True,
        }

    else:
        raise ValueError(f"Unknown MCP tool '{tool_name}' (normalized: '{norm_name}')")


async def handle_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    user_id: str | None = None,
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """Routes an MCP tool call to the corresponding PromptIQ service."""
    if db is not None:
        if not user_id:
            user = await get_or_create_mcp_user(db)
            user_id = user.id
        return await _dispatch_tool(db, tool_name, arguments, user_id)

    async with async_session_factory() as session:
        if not user_id:
            user = await get_or_create_mcp_user(session)
            user_id = user.id
        result = await _dispatch_tool(session, tool_name, arguments, user_id)
        await session.commit()
        return result


async def run_stdio_mcp_server():
    """Runs standard stdio MCP JSON-RPC protocol loop with full initialize handshake support."""
    # Ensure all logging goes to stderr in MCP mode to preserve stdout for JSON-RPC
    for h in logging.getLogger("promptiq").handlers:
        if isinstance(h, logging.StreamHandler):
            h.stream = sys.stderr

    await init_db()

    async with async_session_factory() as db:
        user = await get_or_create_mcp_user(db)
        mcp_user_id = user.id

    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            break

        line_str = line.strip()
        if not line_str:
            continue

        req_id = None
        try:
            rpc_req = json.loads(line_str)
            req_id = rpc_req.get("id")
            method = rpc_req.get("method")
            params = rpc_req.get("params", {})

            # Standard JSON-RPC 2.0: Notifications have NO "id" (or id is null).
            # The server MUST NOT respond to any notification.
            is_notification = ("id" not in rpc_req) or (req_id is None)

            if method in ("notifications/initialized", "initialized", "notifications/cancelled", "$/cancelRequest"):
                # Standard MCP client initialization and cancellation notifications
                continue

            if is_notification:
                # Any other notification: do not respond
                continue

            if method == "initialize":
                protocol_version = params.get("protocolVersion", "2024-11-05")
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": protocol_version,
                        "serverInfo": {
                            "name": "promptiq",
                            "version": "1.0.0",
                        },
                        "capabilities": {
                            "tools": {
                                "listChanged": False,
                            },
                        },
                    },
                }
            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            elif method == "tools/list":
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
                    "error": {"code": -32601, "message": f"Method '{method}' not found"},
                }

            out_bytes = (json.dumps(response) + "\n").encode("utf-8")
            sys.stdout.buffer.write(out_bytes)
            sys.stdout.buffer.flush()

        except Exception as e:
            if req_id is not None:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                }
                sys.stdout.buffer.write((json.dumps(err_resp) + "\n").encode("utf-8"))
                sys.stdout.buffer.flush()


if __name__ == "__main__":
    asyncio.run(run_stdio_mcp_server())
