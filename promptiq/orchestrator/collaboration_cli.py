"""Safe Command-Line Runner for Live Multi-Model Collaboration Workflow.

Executes real hosted multi-model collaboration across:
- Model A: openai/gpt-oss-120b (Specialist Generator)
- Model B: openai/gpt-oss-20b (Independent Critic Specialist)

Strictly requires explicit opt-in (--opt-in) and operator free-plan confirmation.
Never logs credentials, authorization headers, or private user data.
Enforces zero mock fallbacks during live execution.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from promptiq.core.config import settings
from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.core.logging import logger
from promptiq.gateway.account_verification import (
    OperatorAccountVerifier,
    OperatorConfirmationRequiredError,
)
from promptiq.gateway.eligibility import verify_zero_price_route
from promptiq.orchestrator.collaboration import MultiModelCollaborationPipeline
from promptiq.schemas.model_pool import (
    DataSensitivityLevel,
    ExecutionProfile,
    MultiModelExecutionAuditRecord,
)

DEFAULT_COLLABORATION_TASK = (
    "Design a backend-only Food Donation and Surplus Food Redistribution Platform.\n\n"
    "It must connect donors with eligible NGOs and recipient organisations.\n\n"
    "Include:\n"
    "- Food listings.\n"
    "- Expiry tracking.\n"
    "- Pickup coordination.\n"
    "- Organisation verification.\n"
    "- Notifications.\n"
    "- Inventory management.\n"
    "- Role-based access control.\n"
    "- Food-safety rules.\n"
    "- Fraud prevention.\n"
    "- Audit history.\n"
    "- Data privacy.\n"
    "- Acceptance criteria.\n\n"
    "Do not create a frontend."
)


async def execute_live_collaboration(
    opt_in: bool = False,
    task_prompt: str | None = None,
    profile: ExecutionProfile = ExecutionProfile.STANDARD,
    output_json_path: str | None = "docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json",
) -> tuple[str, MultiModelExecutionAuditRecord | None, dict[str, Any]]:
    """Executes the live 5-stage collaboration pipeline with verified hosted models."""
    prompt = task_prompt or DEFAULT_COLLABORATION_TASK

    # 1. Zero-price invariant checks for both models
    verify_zero_price_route(provider="groq", model_id="openai/gpt-oss-120b", price_per_token=0.0)
    verify_zero_price_route(provider="groq", model_id="openai/gpt-oss-20b", price_per_token=0.0)

    # 2. Operator account confirmation gate
    try:
        verification_record = OperatorAccountVerifier.verify_operator_account(
            provider="groq",
            model_id="openai/gpt-oss-120b",
            opt_in_confirmed=opt_in,
        )
    except OperatorConfirmationRequiredError as e:
        logger.info("Live collaboration held: %s", e.message)
        error_result = {
            "status": "BLOCKED_EXTERNAL",
            "provider": "groq",
            "success": False,
            "error": e.message,
            "notice": "Real operator credentials, free tier confirmation, and explicit --opt-in required. Never substitute mock execution.",
        }
        return "", None, error_result

    # 3. Enforce fail-closed inference (no mock fallback allowed during live collaboration)
    settings.MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK = False
    settings.MANAGED_INFERENCE_PRIMARY_ROUTE = "groq"

    api_key = settings.effective_groq_api_key
    if not api_key:
        error_result = {
            "status": "BLOCKED_EXTERNAL",
            "provider": "groq",
            "success": False,
            "error": "No operator Groq API key available in process environment. Failing closed.",
            "notice": "Provide API key via in-memory secure launcher scripts/run_groq_collaboration_secure.ps1.",
        }
        return "", None, error_result

    # 4. Execute 5-Stage Multi-Model Collaboration Pipeline
    try:
        final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
            task_id="collab-live-food-redistribution-1",
            project_id="proj-live-collab",
            user_id="operator",
            prompt=prompt,
            profile=profile,
            sensitivity=DataSensitivityLevel.GENERAL,
            preferred_provider="groq",
        )
    except CapacityExhaustedError as e:
        error_result = {
            "status": "CAPACITY_EXHAUSTED",
            "provider": "groq",
            "success": False,
            "error": f"Collaboration halted by governor: {e.message}",
            "details": e.details,
        }
        return "", None, error_result
    except Exception as e:
        err_str = str(e).replace(api_key, "[REDACTED_API_KEY]") if api_key else str(e)
        error_result = {
            "status": "EXECUTION_ERROR",
            "provider": "groq",
            "success": False,
            "error": err_str,
        }
        return "", None, error_result

    # 5. Build Comprehensive Output Ledger
    summary = {
        "status": "SUCCESS" if audit.final_status == "SUCCESS" else "FAILED",
        "workflow_id": audit.workflow_id,
        "task_id": audit.task_id,
        "execution_profile": audit.execution_profile.value,
        "generator_model": audit.generator_model_id,
        "critic_model": audit.critic_model_id,
        "is_multi_model": audit.is_multi_model,
        "is_multi_family": audit.is_multi_family,
        "is_multi_provider": audit.is_multi_provider,
        "model_diversity_rating": audit.model_diversity_rating,
        "consensus_status": audit.consensus_status,
        "total_latency_ms": audit.total_latency_ms,
        "total_tokens": audit.total_tokens,
        "deterministic_verification_passed": audit.deterministic_verification_passed,
        "account_verification_state": verification_record.verification_state,
        "steps_count": len(audit.steps),
        "resolution_breakdown": audit.resolution_breakdown,
        "steps": [s.model_dump(mode="json") for s in audit.steps],
    }

    # 6. Save execution record to disk if path requested
    if output_json_path:
        out_file = Path(output_json_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        dump_data = {
            "summary": summary,
            "initial_artifact": audit.initial_artifact,
            "critic_review": audit.critic_review,
            "revised_artifact": audit.revised_artifact,
            "final_text": final_text,
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, indent=2, default=str)
        logger.info("Saved collaboration execution results to %s", output_json_path)

    return final_text, audit, summary


def main() -> None:
    """CLI entrypoint for executing live multi-model collaboration."""
    parser = argparse.ArgumentParser(description="PromptIQ Live Multi-Model Collaboration Runner")
    parser.add_argument("--opt-in", action="store_true", help="Explicitly opt-in to send live network requests.")
    parser.add_argument("--profile", default="STANDARD", choices=["STANDARD", "DEEP", "HIGH_RISK", "QUICK"], help="Execution profile.")
    parser.add_argument("--prompt", default=None, help="Custom prompt or use standard food redistribution platform task.")
    parser.add_argument("--output", default="docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json", help="Path to save execution ledger.")

    args = parser.parse_args()

    print("=" * 70)
    print("PROMPTIQ LIVE MULTI-MODEL COLLABORATION RUNNER")
    print("=" * 70)
    print(f"Profile:        {args.profile}")
    print(f"Opt-In Status:  {args.opt_in}")
    print(f"Output File:    {args.output}")
    print("Stage Sequence: Stage A (Gen) -> Stage B (Critic) -> Stage C (Det Verif) -> Stage D (Rev) -> Stage E (Final Verif)")
    print("=" * 70)

    exec_profile = ExecutionProfile(args.profile)
    final_text, audit, summary = asyncio.run(execute_live_collaboration(
        opt_in=args.opt_in,
        task_prompt=args.prompt,
        profile=exec_profile,
        output_json_path=args.output,
    ))

    print(f"\nExecution Status: {summary.get('status')}")
    if not audit:
        print(f"Failure Reason:   {summary.get('error')}")
        if summary.get("notice"):
            print(f"Notice:           {summary.get('notice')}")
        sys.exit(1 if summary.get("status") != "BLOCKED_EXTERNAL" else 2)

    print(f"Workflow ID:      {audit.workflow_id}")
    print(f"Total Latency:    {audit.total_latency_ms} ms")
    print(f"Total Tokens:     {audit.total_tokens}")
    print(f"Consensus Status: {audit.consensus_status}")
    print(f"Deterministic:    {'PASSED' if audit.deterministic_verification_passed else 'FAILED'}")
    print("\n--- Model Diversity Disclosures ---")
    print(f"is_multi_model:         {audit.is_multi_model}")
    print(f"is_multi_family:        {audit.is_multi_family}")
    print(f"is_multi_provider:      {audit.is_multi_provider}")
    print(f"model_diversity_rating: {audit.model_diversity_rating}")

    print("\n--- Multi-Model Execution Step Trace ---")
    print(f"{'Step':<5} {'Role':<18} {'Model':<24} {'Req ID':<32} {'HTTP':<6} {'Latency (ms)':<14} {'Tokens'}")
    print("-" * 110)
    for s in audit.steps:
        req_id_display = s.request_id or "internal"
        tokens_display = f"{s.input_tokens}/{s.output_tokens}"
        print(f"{s.step_number:<5} {s.role.value:<18} {s.model_id:<24} {req_id_display:<32} {s.http_status:<6} {s.latency_ms:<14} {tokens_display}")

    if audit.resolution_breakdown:
        res = audit.resolution_breakdown
        print("\n--- Resolution Breakdown ---")
        print(f"Resolved Findings ({len(res.get('resolved', []))}):")
        for f in res.get("resolved", [])[:5]:
            print(f"  [RESOLVED] {f[:90]}...")
        if len(res.get("resolved", [])) > 5:
            print(f"  ... and {len(res.get('resolved', [])) - 5} more")

        print(f"\nRejected with Reason ({len(res.get('rejected_with_reason', []))}):")
        for f in res.get("rejected_with_reason", []):
            print(f"  [REJECTED] {f[:90]}...")

        print(f"\nUnresolved Findings ({len(res.get('unresolved', []))}):")
        for f in res.get("unresolved", []):
            print(f"  [UNRESOLVED] {f[:90]}...")

    print("\n" + "=" * 70)
    print("LIVE COLLABORATION COMPLETE")
    print(f"Full execution artifact written to: {args.output}")
    print("=" * 70)


if __name__ == "__main__":
    main()
