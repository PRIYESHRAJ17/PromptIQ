"""Command Line Interface for PromptIQ."""

import argparse
import asyncio
import json
import secrets
from pathlib import Path
from typing import Any

from promptiq.compiler.target_compiler import target_compiler
from promptiq.core.database import async_session_factory, init_db
from promptiq.core.logging import logger
from promptiq.core.security import get_password_hash
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.discovery.adaptive import AdaptiveDiscoveryEngine
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.governor import capacity_governor
from promptiq.mcp.server import run_stdio_mcp_server
from promptiq.registry.model_registry import ModelRegistryService
from promptiq.schemas.critic import AutopsyRequest
from promptiq.schemas.discovery import InitialIntakeRequest
from promptiq.schemas.project import ProjectCreate
from promptiq.services.project_service import ProjectService


async def _get_or_create_cli_user(session) -> Any:
    """Resolves or provisions a local default user and workspace for CLI operations."""
    from sqlalchemy import select

    from promptiq.models.user import User, Workspace, WorkspaceMembership

    stmt = select(User).where(User.email == "cli@promptiq.org")
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        user = User(
            email="cli@promptiq.org",
            hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            full_name="PromptIQ CLI User",
            is_active=True,
            is_superuser=True,
        )

        session.add(user)
        await session.flush()

        ws = Workspace(
            name="CLI Workspace",
            owner_id=user.id,
        )
        session.add(ws)
        await session.flush()

        mem = WorkspaceMembership(
            workspace_id=ws.id,
            user_id=user.id,
            role="owner",
        )
        session.add(mem)
        await session.flush()
    return user


def cli_entrypoint():
    """CLI entry point for terminal interaction."""
    parser = argparse.ArgumentParser(
        prog="promptiq",
        description="PromptIQ: Universal Prompt Intelligence & Cross-Agent Continuity CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # init
    subparsers.add_parser("init", help="Initialize the local database and environment")

    # mcp
    subparsers.add_parser(
        "mcp", help="Launch the PromptIQ Model Context Protocol (MCP) stdio server"
    )

    # status
    subparsers.add_parser("status", help="Display zero-price gateway and capacity status")

    # quota
    quota_parser = subparsers.add_parser(
        "quota", help="Display real-time model quota usage and limits"
    )
    quota_parser.add_argument("--model", default=None, help="Specific model ID to inspect")

    # review
    review_parser = subparsers.add_parser("review", help="Run prompt autopsy on text or a file")
    review_parser.add_argument("prompt", help="Prompt text or file path")
    review_parser.add_argument("--target", default="google-antigravity", help="Target environment")

    # recommend
    rec_parser = subparsers.add_parser(
        "recommend", help="Recommend optimal target execution environment"
    )
    rec_parser.add_argument("requirements", help="Requirements text or description")

    # export
    export_parser = subparsers.add_parser("export", help="Export full project data bundle as JSON")
    export_parser.add_argument("project_id", help="Project ID to export")
    export_parser.add_argument("--output", "-o", default=None, help="File path to save JSON bundle")

    # projects
    proj_parser = subparsers.add_parser("projects", help="Manage PromptIQ projects")
    proj_sub = proj_parser.add_subparsers(dest="proj_command", help="Project operations")

    proj_sub.add_parser("list", help="List all projects")

    proj_create = proj_sub.add_parser("create", help="Create a new project")
    proj_create.add_argument("--name", required=True, help="Project name")
    proj_create.add_argument("--description", "-d", default=None, help="Project description")

    proj_exp = proj_sub.add_parser("export", help="Export project data bundle")
    proj_exp.add_argument("project_id", help="Project ID to export")
    proj_exp.add_argument("--output", "-o", default=None, help="File path to save JSON bundle")

    # discovery
    disc_parser = subparsers.add_parser("discovery", help="Run conversational discovery")
    disc_sub = disc_parser.add_subparsers(dest="disc_command", help="Discovery operations")
    disc_start = disc_sub.add_parser("start", help="Start a new discovery session")
    disc_start.add_argument("--project", required=True, help="Project ID")
    disc_start.add_argument("--intent", required=True, help="High-level user intent")
    disc_start.add_argument(
        "--mode", default="guided", choices=["quick", "guided", "deep"], help="Discovery mode"
    )

    args = parser.parse_args()

    if args.command == "init":

        async def _init():
            await init_db()
            async with async_session_factory() as session:
                await _get_or_create_cli_user(session)
                await session.commit()
            print("PromptIQ database initialized successfully with default CLI workspace.")

        asyncio.run(_init())

    elif args.command == "mcp":
        asyncio.run(run_stdio_mcp_server())

    elif args.command == "status":
        quota = inference_gateway.get_quota_status()
        print("\n=== PROMPTIQ CAPACITY & INFERENCE STATUS ===")
        print(f"Active Provider Route: {quota.provider}")
        print(
            f"Zero-Price Policy: {'ACTIVE ($0)' if quota.zero_price_policy_active else 'INACTIVE'}"
        )
        print(f"Route Status: {'PAUSED' if quota.is_paused else 'HEALTHY / ACTIVE'}")
        if quota.is_paused:
            print(f"Pause Reason: {quota.pause_reason}")
        print(f"Notice: {quota.notice}\n")

    elif args.command == "quota":
        models_to_check = (
            [args.model]
            if args.model
            else [m.model_id for m in ModelRegistryService.list_models(zero_price_only=True)]
        )
        print("\n=== PROMPTIQ REAL-TIME MODEL QUOTA LEDGER ===")

        header = f"{'MODEL ID':<25} | {'RPM USED':<9} | {'TPM USED / LIMIT':<20} | {'RESERVED':<8} | {'RESET':<7} | {'STATUS'}"
        print(header)
        print("-" * len(header))
        for m_id in models_to_check:
            st = capacity_governor.get_model_quota_status(m_id)
            status_str = "RATE-LIMITED" if st["is_rate_limited"] else "HEALTHY"
            tpm_str = f"{st['tpm_used']} / {st['tpm_limit']}"
            rpm_str = f"{st['rpm_used']}/{st['rpm_limit']}"
            reset_str = f"{st['reset_seconds']}s" if st["reset_seconds"] > 0 else "0s"
            print(
                f"{m_id:<25} | {rpm_str:<9} | {tpm_str:<20} | {st.get('reserved_tokens', 0):<8} | {reset_str:<7} | {status_str}"
            )
        print()

    elif args.command == "review":
        prompt_text = args.prompt
        try:
            with open(args.prompt, encoding="utf-8") as f:
                prompt_text = f.read()
        except (OSError, UnicodeDecodeError):
            logger.debug(
                f"Input '{args.prompt}' is not a local file path; evaluating as inline prompt text."
            )

        async def _run_review():
            res = await PromptAutopsyEngine.diagnose_prompt(
                AutopsyRequest(prompt_text=prompt_text, target_environment=args.target)
            )
            print("\n=== PROMPT AUTOPSY DIAGNOSTIC ===")
            print(f"Verdict: {res.verdict.upper()}")
            print(f"Summary: {res.summary}")
            print("\nFindings:")
            for f in res.findings:
                print(f"- [{f.severity.upper()}] {f.finding}")
                print(f"  Recommendation: {f.recommendation}")
            print("\nScores:")
            for k, v in res.quality_scores.items():
                print(f"  {k}: {v}%")

        asyncio.run(_run_review())

    elif args.command == "recommend":
        rec = target_compiler.recommend_target(args.requirements)
        print("\n=== TARGET ENVIRONMENT RECOMMENDATION ===")
        print(f"Recommended Target: {rec['recommended_target']}")
        print(f"Rationale: {rec['rationale']}\n")
        print("Pros:")
        for p in rec["pros"]:
            print(f"  + {p}")
        print("Cons:")
        for c in rec["cons"]:
            print(f"  - {c}")
        print("\nCompatibility Scores:")
        for k, v in rec["compatibility_scores"].items():
            print(f"  {k}: {int(v * 100)}%")
        print()

    elif args.command == "export" or (
        args.command == "projects" and getattr(args, "proj_command", None) == "export"
    ):
        project_id = args.project_id
        output_file = args.output

        async def _run_export():
            await init_db()
            async with async_session_factory() as session:
                user = await _get_or_create_cli_user(session)
                data = await ProjectService.export_project_data(session, project_id, user.id)
                payload_str = json.dumps(data, indent=2)
                if output_file:
                    Path(output_file).write_text(payload_str, encoding="utf-8")
                    print(f"Project '{project_id}' successfully exported to {output_file}.")
                else:
                    print(payload_str)

        asyncio.run(_run_export())

    elif args.command == "projects":
        cmd = getattr(args, "proj_command", None)
        if cmd == "list":

            async def _run_list():
                await init_db()
                async with async_session_factory() as session:
                    user = await _get_or_create_cli_user(session)
                    projs = await ProjectService.list_projects(session, user.id)
                    print("\n=== PROMPTIQ PROJECTS ===")
                    if not projs:
                        print(
                            "No projects found. Create one with: promptiq projects create --name <NAME>"
                        )
                    else:
                        for p in projs:
                            print(
                                f"- {p.name} (ID: {p.id}, Version: v{p.current_constitution_version})"
                            )
                    print()

            asyncio.run(_run_list())

        elif cmd == "create":

            async def _run_create():
                await init_db()
                async with async_session_factory() as session:
                    user = await _get_or_create_cli_user(session)
                    proj = await ProjectService.create_project(
                        session,
                        user.id,
                        ProjectCreate(name=args.name, description=args.description),
                        surface="cli",
                    )
                    await session.commit()
                    print(f"\nCreated Project '{proj.name}' successfully.")
                    print(f"Project ID: {proj.id}")
                    print(f"Initial Constitution Version: v{proj.current_constitution_version}\n")

            asyncio.run(_run_create())

        else:
            parser.parse_args(["projects", "--help"])

    elif args.command == "discovery":
        cmd = getattr(args, "disc_command", None)
        if cmd == "start":

            async def _run_disc_start():
                await init_db()
                async with async_session_factory() as session:
                    user = await _get_or_create_cli_user(session)
                    resp = await AdaptiveDiscoveryEngine.start_discovery_session(
                        session,
                        project_id=args.project,
                        user_id=user.id,
                        intake=InitialIntakeRequest(intent=args.intent, mode=args.mode),
                        surface="cli",
                    )
                    await session.commit()

                    print(f"\n=== DISCOVERY SESSION STARTED ({resp.session_id}) ===")
                    print(f"Mode: {resp.mode.upper()}")
                    print(f"Status: {resp.status.upper()}")
                    if resp.current_question:
                        print(f"\nNext Question ({resp.current_question.id}):")
                        print(f"{resp.current_question.question}")
                        if resp.current_question.why_asked:
                            print(f"Why Asked: {resp.current_question.why_asked}")
                        if resp.current_question.options:
                            print("Options:")
                            for opt in resp.current_question.options:
                                print(f"  * {opt}")
                    print()

            asyncio.run(_run_disc_start())
        else:
            parser.parse_args(["discovery", "--help"])

    else:
        parser.print_help()


if __name__ == "__main__":
    cli_entrypoint()
