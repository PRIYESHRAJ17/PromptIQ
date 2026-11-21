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
        "status": audit.final_status,
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
        "stage_statuses": audit.stage_statuses,
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


async def resume_live_collaboration(
    workflow_id: str,
    opt_in: bool = False,
    output_json_path: str = "docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json",
) -> tuple[str, MultiModelExecutionAuditRecord | None, dict[str, Any]]:
    """Resumes a partially completed live collaboration workflow at Stage D (Revision)."""
    # 1. Zero-price invariant checks
    verify_zero_price_route(provider="groq", model_id="openai/gpt-oss-120b", price_per_token=0.0)

    # 2. Operator account confirmation gate
    try:
        verification_record = OperatorAccountVerifier.verify_operator_account(
            provider="groq",
            model_id="openai/gpt-oss-120b",
            opt_in_confirmed=opt_in,
        )
    except OperatorConfirmationRequiredError as e:
        logger.info("Live collaboration resumption held: %s", e.message)
        error_result = {
            "status": "BLOCKED_EXTERNAL",
            "provider": "groq",
            "success": False,
            "error": e.message,
            "notice": "Real operator credentials, free tier confirmation, and explicit --opt-in required. Never substitute mock execution.",
        }
        return "", None, error_result

    # 3. Enforce fail-closed inference
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

    # 4. Resume workflow
    try:
        final_text, audit = await MultiModelCollaborationPipeline.resume_workflow_revision(
            workflow_id=workflow_id,
            user_id="operator",
            persisted_json_path=output_json_path,
            preferred_provider="groq",
        )
    except CapacityExhaustedError as e:
        error_result = {
            "status": "CAPACITY_EXHAUSTED",
            "provider": "groq",
            "success": False,
            "error": f"Collaboration resumption held by governor: {e.message}",
            "details": e.details,
            "retry_after": e.retry_after,
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

    summary = {
        "status": audit.final_status,
        "workflow_id": workflow_id,
        "resumed_workflow_id": audit.workflow_id,
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
        "stage_statuses": audit.stage_statuses,
        "resolution_breakdown": audit.resolution_breakdown,
        "steps": [s.model_dump(mode="json") for s in audit.steps],
    }

    return final_text, audit, summary


def format_str(val: Any, default: str = "N/A") -> str:
    """Safely format string or fallback to default."""
    if val is None or val == "":
        return default
    return str(val)


def format_http_status(status: int | None, provider: str | None = None) -> str:
    """Format HTTP status, rendering internal steps and None as N/A."""
    if provider == "internal":
        return "N/A"
    if status is None:
        return "N/A"
    return str(status)


def format_request_id(req_id: str | None, provider: str | None = None) -> str:
    """Format request ID, distinguishing internal steps from external."""
    if provider == "internal":
        return "N/A (Internal)"
    if not req_id:
        return "N/A"
    return str(req_id)


def format_latency(latency_ms: float | int | None) -> str:
    """Safely format latency in milliseconds."""
    if latency_ms is None:
        return "N/A"
    try:
        return f"{float(latency_ms):.1f}"
    except (ValueError, TypeError):
        return "N/A"


def format_tokens(
    in_tokens: int | None, out_tokens: int | None, provider: str | None = None
) -> str:
    """Safely format token pair."""
    if provider == "internal":
        return "0/0"
    in_str = str(in_tokens) if in_tokens is not None else "N/A"
    out_str = str(out_tokens) if out_tokens is not None else "N/A"
    return f"{in_str}/{out_str}"


def format_provider(provider: str | None) -> str:
    """Format provider name, marking internal steps clearly."""
    if not provider or provider == "internal":
        return "[INTERNAL]"
    return provider.lower()


def format_timestamp(ts: Any) -> str:
    """Safely format datetime timestamp or string."""
    if ts is None:
        return "N/A"
    if hasattr(ts, "isoformat"):
        return ts.isoformat()
    return str(ts)


def render_execution_summary(
    audit: MultiModelExecutionAuditRecord | None,
    summary: dict[str, Any],
    output_path: str | None = None,
) -> None:
    """Safely renders collaboration execution summary and step trace with null-safe formatting."""
    print(f"\nExecution Status: {summary.get('status', 'UNKNOWN')}")
    if not audit:
        print(f"Failure Reason:   {summary.get('error', 'Unknown failure')}")
        if summary.get("notice"):
            print(f"Notice:           {summary.get('notice')}")
        return

    parent_id = getattr(audit, "parent_workflow_id", None) or summary.get("workflow_id")
    resumed_id = summary.get("resumed_workflow_id") or (
        audit.workflow_id if parent_id and parent_id != audit.workflow_id else None
    )

    if parent_id and resumed_id and parent_id != resumed_id:
        print(f"Workflow ID:      {parent_id}")
        print(f"Resumed ID:       {resumed_id}")
    else:
        print(f"Workflow ID:      {audit.workflow_id or parent_id or 'N/A'}")

    total_lat = getattr(audit, "total_latency_ms", None)
    lat_str = format_latency(total_lat)
    print(f"Total Latency:    {lat_str} ms" if lat_str != "N/A" else "Total Latency:    N/A")
    print(f"Total Tokens:     {format_str(getattr(audit, 'total_tokens', None))}")
    print(f"Consensus Status: {format_str(getattr(audit, 'consensus_status', None))}")
    det_passed = getattr(audit, "deterministic_verification_passed", None)
    if det_passed is None:
        det_str = "N/A"
    else:
        det_str = "PASSED" if det_passed else "FAILED"
    print(f"Deterministic:    {det_str}")
    print("\n--- Model Diversity Disclosures ---")
    print(f"is_multi_model:         {getattr(audit, 'is_multi_model', 'N/A')}")
    print(f"is_multi_family:        {getattr(audit, 'is_multi_family', 'N/A')}")
    print(f"is_multi_provider:      {getattr(audit, 'is_multi_provider', 'N/A')}")
    print(f"model_diversity_rating: {getattr(audit, 'model_diversity_rating', 'N/A')}")

    print("\n--- Multi-Model Execution Step Trace ---")
    print(
        f"{'Step':<5} {'Role':<18} {'Provider':<12} {'Model':<26} {'Req ID':<32} {'HTTP':<6} {'Latency (ms)':<14} {'Tokens'}"
    )
    print("-" * 122)
    for s in audit.steps:
        prov = getattr(s, "provider", None) or "internal"
        role_val = s.role.value if hasattr(s.role, "value") else str(s.role)
        prov_disp = format_provider(prov)
        model_disp = format_str(getattr(s, "model_id", None))
        req_disp = format_request_id(getattr(s, "request_id", None), prov)
        http_disp = format_http_status(getattr(s, "http_status", None), prov)
        lat_disp = format_latency(getattr(s, "latency_ms", None))
        tok_disp = format_tokens(
            getattr(s, "input_tokens", None),
            getattr(s, "output_tokens", None),
            prov,
        )

        step_num = getattr(s, "step_number", "?")
        print(
            f"{step_num:<5} "
            f"{role_val:<18} "
            f"{prov_disp:<12} "
            f"{model_disp:<26} "
            f"{req_disp:<32} "
            f"{http_disp:<6} "
            f"{lat_disp:<14} "
            f"{tok_disp}"
        )

    res = getattr(audit, "resolution_breakdown", None) or summary.get("resolution_breakdown", {})
    if res:
        resolved = res.get("resolved", [])
        if resolved:
            print("\n--- Resolution Breakdown ---")
            print(f"Resolved Findings ({len(resolved)}):")
            for f in resolved[:5]:
                print(f"  [RESOLVED] {f[:90]}...")
            if len(resolved) > 5:
                print(f"  ... and {len(resolved) - 5} more")

        rejected = res.get("rejected_with_reason", [])
        if rejected:
            print(f"\nRejected with Reason ({len(rejected)}):")
            for f in rejected:
                print(f"  [REJECTED] {f[:90]}...")

        unresolved = res.get("unresolved", [])
        if unresolved:
            print(f"\nUnresolved Findings ({len(unresolved)}):")
            for f in unresolved:
                print(f"  [UNRESOLVED] {f[:90]}...")

    if output_path:
        print("\n" + "=" * 70)
        print("LIVE COLLABORATION COMPLETE")
        print(f"Full execution artifact written to: {output_path}")
        print("=" * 70)


def main() -> None:
    """CLI entrypoint for executing live multi-model collaboration."""
    parser = argparse.ArgumentParser(description="PromptIQ Live Multi-Model Collaboration Runner")
    parser.add_argument(
        "--opt-in", action="store_true", help="Explicitly opt-in to send live network requests."
    )
    parser.add_argument(
        "--profile",
        default="STANDARD",
        choices=["STANDARD", "DEEP", "HIGH_RISK", "QUICK"],
        help="Execution profile.",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Custom prompt or use standard food redistribution platform task.",
    )
    parser.add_argument(
        "--output",
        default="docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json",
        help="Path to save execution ledger.",
    )
    parser.add_argument(
        "--resume",
        default=None,
        help="Workflow ID of partially completed workflow to resume at Stage D.",
    )
    parser.add_argument(
        "--inspect",
        nargs="?",
        const="docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json",
        default=None,
        help="Inspect and display formatted execution summary from a saved JSON ledger without making any API calls.",
    )

    args = parser.parse_args()

    # If --inspect requested, display formatted summary and exit cleanly without network calls
    if args.inspect:
        inspect_file = Path(args.inspect)
        if not inspect_file.exists():
            print(f"Error: Inspect file not found: {inspect_file}")
            sys.exit(1)
        with open(inspect_file, encoding="utf-8") as f:
            data = json.load(f)
        summary = data.get("summary", data)
        try:
            audit = MultiModelExecutionAuditRecord.model_validate(summary)
        except Exception as e:
            logger.debug("Could not validate audit record directly: %s", e)
            audit = None
        render_execution_summary(audit, summary, output_path=str(inspect_file))
        return

    print("=" * 70)
    print("PROMPTIQ LIVE MULTI-MODEL COLLABORATION RUNNER")
    print("=" * 70)
    if args.resume:
        print(f"Action:         RESUME WORKFLOW ({args.resume})")
        print("Stage Sequence: Skip A/B/C -> Stage D (120B Rev) -> Stage E (Final Verif)")
    else:
        print(f"Profile:        {args.profile}")
        print(
            "Stage Sequence: Stage A (Gen) -> Stage B (Critic) -> Stage C (Det Verif) -> Stage D (Rev) -> Stage E (Final Verif)"
        )
    print(f"Opt-In Status:  {args.opt_in}")
    print(f"Output File:    {args.output}")
    print("=" * 70)

    if args.resume:
        final_text, audit, summary = asyncio.run(
            resume_live_collaboration(
                workflow_id=args.resume,
                opt_in=args.opt_in,
                output_json_path=args.output,
            )
        )
    else:
        exec_profile = ExecutionProfile(args.profile)
        final_text, audit, summary = asyncio.run(
            execute_live_collaboration(
                opt_in=args.opt_in,
                task_prompt=args.prompt,
                profile=exec_profile,
                output_json_path=args.output,
            )
        )

    render_execution_summary(audit, summary, output_path=args.output)
    if not audit:
        sys.exit(1 if summary.get("status") != "BLOCKED_EXTERNAL" else 2)


if __name__ == "__main__":
    main()
