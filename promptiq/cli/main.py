"""Command Line Interface for PromptIQ."""

import argparse
import asyncio

from promptiq.core.database import init_db
from promptiq.core.logging import logger
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.gateway.gateway import inference_gateway
from promptiq.mcp.server import run_stdio_mcp_server
from promptiq.schemas.critic import AutopsyRequest


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
    subparsers.add_parser("mcp", help="Launch the PromptIQ Model Context Protocol (MCP) stdio server")

    # status
    subparsers.add_parser("status", help="Display zero-price gateway and capacity status")

    # review
    review_parser = subparsers.add_parser("review", help="Run prompt autopsy on text or a file")
    review_parser.add_argument("prompt", help="Prompt text or file path")
    review_parser.add_argument("--target", default="google-antigravity", help="Target environment")

    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(init_db())
        print("PromptIQ database initialized successfully.")

    elif args.command == "mcp":
        asyncio.run(run_stdio_mcp_server())

    elif args.command == "status":
        quota = inference_gateway.get_quota_status()
        print("\n=== PROMPTIQ CAPACITY & INFERENCE STATUS ===")
        print(f"Active Provider Route: {quota.provider}")
        print(f"Zero-Price Policy: {'ACTIVE ($0)' if quota.zero_price_policy_active else 'INACTIVE'}")
        print(f"Route Status: {'PAUSED' if quota.is_paused else 'HEALTHY / ACTIVE'}")
        if quota.is_paused:
            print(f"Pause Reason: {quota.pause_reason}")
        print(f"Notice: {quota.notice}\n")

    elif args.command == "review":
        prompt_text = args.prompt
        try:
            with open(args.prompt, encoding="utf-8") as f:
                prompt_text = f.read()
        except (OSError, UnicodeDecodeError):
            logger.debug(f"Input '{args.prompt}' is not a local file path; evaluating as inline prompt text.")

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

    else:
        parser.print_help()


if __name__ == "__main__":
    cli_entrypoint()
