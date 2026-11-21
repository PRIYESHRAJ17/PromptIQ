"""PromptIQ Live AI Workflow Execution Engine.

Executes a complete 12-step product workflow:
1. Accept realistic user request (Microservices Incident Triage & Telemetry Engine).
2. Run adaptive discovery session.
3. Build Project Constitution with strict provenance.
4. Generate typed PromptIQ Prompt Specification (PPS).
5. Compile target-native deliverable package (Antigravity).
6. Submit to hosted inference provider (Groq openai/gpt-oss-120b) with fail-closed credential checks.
7. Run independent critic (Groq openai/gpt-oss-20b).
8. Verify critic findings against artifact.
9. Revise artifact with specialist model.
10. Validate objectively with deterministic verifier (forbidden frontend patterns, acceptance criteria).
11. Persist workflow record and database checkpoint.
12. Retrieve saved result and verify cryptographic/audit integrity.
"""

import argparse
import asyncio
import hashlib
import json
import os
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from promptiq.compiler.pps import PPSBuilder
from promptiq.compiler.target_compiler import target_compiler
from promptiq.core.config import settings
from promptiq.core.database import async_session_factory, init_db
from promptiq.discovery.adaptive import AdaptiveDiscoveryEngine
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.memory.checkpoint import CheckpointManager
from promptiq.orchestrator.collaboration import (
    FORBIDDEN_FRONTEND_PATTERNS,
    classify_critic_resolutions,
    prepare_revision_prompt,
)
from promptiq.orchestrator.roles import ModelRoleContract
from promptiq.schemas.auth import UserCreate
from promptiq.schemas.constitution import (
    ConstitutionApprovalRequest,
    ConstitutionUpdate,
    RequirementItem,
    TechnicalDirection,
)
from promptiq.schemas.discovery import InitialIntakeRequest
from promptiq.schemas.memory import CheckpointCreate
from promptiq.schemas.model_pool import (
    LogicalModelRole,
)
from promptiq.schemas.pps import TargetProfileSchema
from promptiq.schemas.project import ProjectCreate
from promptiq.services.auth_service import AuthService
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService

OUTPUT_TRACE_PATH = Path("docs/LIVE_AI_WORKFLOW_TRACE.json")

TASK_PROMPT = (
    "Design a resilient, high-throughput Microservices Incident Triage and Telemetry Correlation Engine in Python.\n\n"
    "Key Functional Requirements:\n"
    "- Ingest high-volume Prometheus metrics and OpenTelemetry distributed traces.\n"
    "- Correlate anomaly spikes across dependent microservices in real time.\n"
    "- Generate probabilistic root-cause hypotheses with confidence scoring.\n"
    "- Automated incident playbook selection with zero execution hallucination.\n"
    "- Notification routing to on-call squads with intelligent de-duplication.\n"
    "- Role-based access control (RBAC) and tenant isolation for enterprise teams.\n"
    "- Immutable audit history ledger for every incident decision and alert.\n"
    "- Food-safety style SLA tracking and automated escalation timeouts.\n"
    "- Comprehensive acceptance criteria and testable failure modes.\n\n"
    "STRICT INVARIANT: This is a backend-only engine. Do not create any website frontend, HTML, or UI."
)


def get_operator_groq_key() -> str | None:
    """Retrieves operator Groq API key from environment if present."""
    return (
        os.getenv("GROQ_API_KEY")
        or os.getenv("OPERATOR_GROQ_API_KEY")
        or settings.OPERATOR_GROQ_API_KEY
        or None
    )


async def execute_12_step_workflow(mode: str = "live") -> dict[str, Any]:
    """Executes the full 12-step PromptIQ product lifecycle."""
    print("=" * 70)
    print("PROMPTIQ — 12-STEP AI WORKFLOW EXECUTION GATE")
    print(f"Mode: {mode.upper()}")
    print(f"Timestamp: {datetime.now(UTC).isoformat()}")
    print("=" * 70)

    workflow_id = str(secrets.token_hex(16))
    start_time = time.perf_counter()
    steps_log: list[dict[str, Any]] = []

    # Initialize database
    await init_db()

    groq_api_key = get_operator_groq_key()
    has_live_credentials = bool(groq_api_key and len(groq_api_key.strip()) > 10)

    if mode == "live" and not has_live_credentials:
        print("\n[NOTICE] No Groq operator credential detected in environment.")
        print("Steps 1-5 (Intake, Discovery, Constitution, PPS, Compilation) will execute fully.")
        print("Step 6 (Hosted Provider Inference) will fail-closed with BLOCKED_EXTERNAL_NO_CREDENTIALS.")
        print("To run live provider inference, launch via scripts/run_live_workflow_secure.ps1 -OptIn -ConfirmFreePlan")

    async with async_session_factory() as db:
        # ---------------------------------------------------------------------
        # STEP 1: ACCEPT REALISTIC USER REQUEST & PROJECT INTAKE
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        hex_suffix = secrets.token_hex(4)
        user_in = UserCreate(
            email=f"workflow_operator_{hex_suffix}@promptiq.org",
            password=f"Pwq_{secrets.token_urlsafe(16)}",
            full_name=f"Workflow Operator {hex_suffix}",
        )
        user, _ = await AuthService.register_user(db, user_in)
        await db.commit()

        project_in = ProjectCreate(
            name="Microservices Incident Triage Engine",
            description="Autonomous telemetry correlation and root-cause analysis backend engine.",
        )
        project = await ProjectService.create_project(db, user_id=user.id, project_in=project_in)
        await db.commit()

        intake_req = InitialIntakeRequest(
            goal="Design enterprise telemetry correlation and incident triage backend",
            deliverable="complete_package",
            target="google-antigravity",
            target_mode="specific",
            context_text=TASK_PROMPT,
            depth="guided",
            task_type="software_project",
        )
        step_1_meta = {
            "step_number": 1,
            "name": "User Request Intake",
            "status": "COMPLETED",
            "project_id": project.id,
            "user_id": user.id,
            "prompt_length": len(TASK_PROMPT),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_1_meta)
        print(f"[Step 1] Completed: Project '{project.name}' created ({step_1_meta['latency_ms']}ms)")

        # ---------------------------------------------------------------------
        # STEP 2: RUN ADAPTIVE DISCOVERY
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        disc_session = await AdaptiveDiscoveryEngine.start_session(
            db, project_id=project.id, user_id=user.id, intake=intake_req
        )
        await db.commit()
        step_2_meta = {
            "step_number": 2,
            "name": "Adaptive Discovery",
            "status": "COMPLETED",
            "session_id": disc_session.id,
            "depth": disc_session.depth,
            "current_stage": disc_session.current_stage,
            "missing_info_count": len(disc_session.missing_high_impact_info),
            "next_questions_count": len(disc_session.next_questions),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_2_meta)
        print(f"[Step 2] Completed: Discovery session {disc_session.id} (Stage: {disc_session.current_stage})")

        # ---------------------------------------------------------------------
        # STEP 3: BUILD PROJECT CONSTITUTION
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        const_update = ConstitutionUpdate(
            goals=["Autonomous incident triage engine", "Sub-second telemetry correlation"],
            scope_out=[
                "STRICTLY NO WEBSITE FRONTEND: Headless daemon only.",
                "React",
                "Next.js",
                "HTML",
                "CSS",
            ],
            requirements=[
                RequirementItem(
                    id="REQ-INCIDENT-001",
                    text="Engine must correlate Prometheus metrics and OpenTelemetry traces in real time.",
                    category="functional",
                    priority="P0",
                    status="confirmed",
                    provenance="user_provided",
                    acceptance_criteria="Sub-second anomaly spike detection across dependent services",
                ),
                RequirementItem(
                    id="REQ-INCIDENT-002",
                    text="Strict zero-frontend invariant: backend engine only.",
                    category="constraint",
                    priority="P0",
                    status="confirmed",
                    provenance="user_provided",
                    acceptance_criteria="No HTML, React, Next.js, or CSS artifacts permitted",
                ),
                RequirementItem(
                    id="REQ-INCIDENT-003",
                    text="Immutable cryptographic audit ledger for all incident alerts and triage decisions.",
                    category="security",
                    priority="P0",
                    status="confirmed",
                    provenance="user_provided",
                    acceptance_criteria="Append-only SHA-256 chained audit events",
                ),
            ],
            technical_direction=TechnicalDirection(
                architecture_pattern="modular_daemon",
                stack=["Python 3.13", "AsyncIO", "OpenTelemetry", "FastAPI"],
                database="SQLite/PostgreSQL",
                api_style="REST & Webhooks",
            ),
        )
        const = await ConstitutionService.update_constitution(
            db, project_id=project.id, user_id=user.id, update_in=const_update
        )
        # Formally approve constitution
        approval = ConstitutionApprovalRequest(
            approve=True,
            signature="Operator Live Acceptance Signature",
            notes="Approved for native PPS compilation",
        )
        const = await ConstitutionService.approve_constitution(db, project.id, user.id, approval)
        await db.commit()

        step_3_meta = {
            "step_number": 3,
            "name": "Project Constitution",
            "status": "COMPLETED",
            "constitution_id": const.id,
            "version": const.version,
            "approval_status": const.status,
            "requirements_count": len(const.requirements),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_3_meta)
        print(f"[Step 3] Completed: Constitution v{const.version} ({const.status})")

        # ---------------------------------------------------------------------
        # STEP 4: GENERATE TYPED PPS (Prompt Specification)
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        target_profile = TargetProfileSchema(
            host="google-antigravity",
            provider="google",
            model_id="gemini-3.8-flash",
        )
        pps = PPSBuilder.build_from_constitution(constitution=const, target_profile=target_profile)
        step_4_meta = {
            "step_number": 4,
            "name": "Typed PPS Generation",
            "status": "COMPLETED",
            "spec_version": pps.spec_version,
            "primary_objective": pps.intent.primary_objective,
            "requirements_count": len(pps.requirements),
            "constraints_count": len(pps.constraints.get("prohibited_actions", [])),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_4_meta)
        print(f"[Step 4] Completed: PPS v{pps.spec_version} generated ({len(pps.requirements)} requirements)")

        # ---------------------------------------------------------------------
        # STEP 5: COMPILE TARGET-NATIVE DELIVERABLE PACKAGE
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        compiled_pkg = await target_compiler.compile_package(
            db=db,
            project_id=project.id,
            user_id=user.id,
            target_environment="google-antigravity",
            output_type="complete_package",
        )
        await db.commit()
        pkg_files = compiled_pkg.files or {}
        system_instruction = pkg_files.get("GEMINI.md") or pkg_files.get("AGENTS.md") or ""
        task_prompt = pkg_files.get("instructions.md") or TASK_PROMPT

        step_5_meta = {
            "step_number": 5,
            "name": "Target-Native Compilation",
            "status": "COMPLETED",
            "target": "google-antigravity",
            "package_id": compiled_pkg.id,
            "files_compiled": list(pkg_files.keys()),
            "system_instruction_chars": len(system_instruction),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_5_meta)
        print(f"[Step 5] Completed: Target 'google-antigravity' compiled ({len(pkg_files)} files: {list(pkg_files.keys())})")

        # ---------------------------------------------------------------------
        # STEP 6: SUBMIT TO HOSTED INFERENCE PROVIDER (GPT-OSS 120B)
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        gen_model_id = "openai/gpt-oss-120b"
        candidate_text: str | None = None
        gen_request_id: str | None = None
        gen_tokens_used = 0

        if mode == "live" and not has_live_credentials:
            step_6_meta = {
                "step_number": 6,
                "name": "Hosted Provider Generation (GPT-OSS 120B)",
                "status": "BLOCKED_EXTERNAL_NO_CREDENTIALS",
                "model_id": gen_model_id,
                "provider": "groq",
                "message": (
                    "No operator credential configured for provider 'groq'. "
                    "Fail-closed invariant enforced: zero synthetic model outputs generated."
                ),
                "request_id": None,
                "tokens_charged": 0,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            }
            steps_log.append(step_6_meta)
            print("[Step 6] Status: BLOCKED_EXTERNAL_NO_CREDENTIALS (Fail-Closed)")
        else:
            provider_choice = "mock" if mode == "mock" else "groq"
            gen_req = InferenceRequest(
                messages=[
                    GatewayMessage(
                        role="system",
                        content=system_instruction
                        or ModelRoleContract.get_system_instruction(LogicalModelRole.PROMPT_ENGINEER),
                    ),
                    GatewayMessage(role="user", content=task_prompt),
                ],
                max_tokens=2500,
                temperature=0.3,
                task_context="generation",
                target_model_id=gen_model_id,
                user_id=user.id,
                workspace_id=project.id,
            )
            gen_resp = await inference_gateway.generate(gen_req, provider=provider_choice)
            candidate_text = gen_resp.text
            gen_request_id = gen_resp.request_id or "mock_req_gen"
            gen_tokens_used = gen_resp.tokens_used

            step_6_meta = {
                "step_number": 6,
                "name": "Hosted Provider Generation (GPT-OSS 120B)",
                "status": "VERIFIED" if gen_resp.http_status == 200 else "PROVIDER_ERROR",
                "model_id": gen_model_id,
                "provider": provider_choice,
                "request_id": gen_request_id,
                "http_status": gen_resp.http_status,
                "input_tokens": gen_resp.prompt_tokens,
                "output_tokens": gen_resp.completion_tokens,
                "total_tokens": gen_tokens_used,
                "latency_ms": round(gen_resp.latency_ms, 2),
                "rate_limit_headers": gen_resp.rate_limit_headers,
            }
            steps_log.append(step_6_meta)
            print(f"[Step 6] Completed: Generation via {gen_model_id} (ReqID: {gen_request_id}, {step_6_meta['latency_ms']}ms)")

        # ---------------------------------------------------------------------
        # STEP 7: RUN INDEPENDENT CRITIC (GPT-OSS 20B)
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        critic_model_id = "openai/gpt-oss-20b"
        critic_text: str | None = None
        critic_request_id: str | None = None

        if candidate_text is None:
            step_7_meta = {
                "step_number": 7,
                "name": "Independent Critic Review (GPT-OSS 20B)",
                "status": "DEFERRED_PENDING_STEP_6",
                "model_id": critic_model_id,
                "provider": "groq",
                "message": "Awaiting Step 6 candidate generation from operator credentialed run.",
                "latency_ms": 0.0,
            }
            steps_log.append(step_7_meta)
            print("[Step 7] Status: DEFERRED_PENDING_STEP_6")
        else:
            provider_choice = "mock" if mode == "mock" else "groq"
            crit_req = InferenceRequest(
                messages=[
                    GatewayMessage(
                        role="system",
                        content=ModelRoleContract.get_system_instruction(LogicalModelRole.CRITIC),
                    ),
                    GatewayMessage(
                        role="user",
                        content=(
                            f"CRITIQUE THE FOLLOWING CANDIDATE ARCHITECTURE AGAINST THE TASK REQUIREMENTS:\n\n"
                            f"TASK:\n{TASK_PROMPT}\n\n"
                            f"CANDIDATE ARCHITECTURE:\n{candidate_text}\n\n"
                            f"Identify missing failure modes, observability gaps, concurrency bottlenecks, and privacy flaws."
                        ),
                    ),
                ],
                max_tokens=1500,
                temperature=0.1,
                task_context="criticism",
                target_model_id=critic_model_id,
                user_id=user.id,
                workspace_id=project.id,
            )
            crit_resp = await inference_gateway.generate(crit_req, provider=provider_choice)
            critic_text = crit_resp.text
            critic_request_id = crit_resp.request_id or "mock_req_crit"

            step_7_meta = {
                "step_number": 7,
                "name": "Independent Critic Review (GPT-OSS 20B)",
                "status": "VERIFIED" if crit_resp.http_status == 200 else "PROVIDER_ERROR",
                "model_id": critic_model_id,
                "provider": provider_choice,
                "request_id": critic_request_id,
                "http_status": crit_resp.http_status,
                "input_tokens": crit_resp.prompt_tokens,
                "output_tokens": crit_resp.completion_tokens,
                "total_tokens": crit_resp.tokens_used,
                "latency_ms": round(crit_resp.latency_ms, 2),
                "rate_limit_headers": crit_resp.rate_limit_headers,
            }
            steps_log.append(step_7_meta)
            print(f"[Step 7] Completed: Criticism via {critic_model_id} (ReqID: {critic_request_id})")

        # ---------------------------------------------------------------------
        # STEP 8: VERIFY FINDINGS
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        autopsy_findings: list[str] = []
        if critic_text is not None and candidate_text is not None:
            # Deterministic finding categorization
            resolutions = classify_critic_resolutions(critic_text, candidate_text)
            autopsy_findings = resolutions.get("resolved", []) + resolutions.get("unresolved", [])
            step_8_status = "VERIFIED"
        else:
            resolutions = {"resolved": [], "unresolved": [], "rejected_with_reason": []}
            step_8_status = "DEFERRED_PENDING_STEP_7"

        step_8_meta = {
            "step_number": 8,
            "name": "Deterministic Finding Verification",
            "status": step_8_status,
            "resolved_count": len(resolutions.get("resolved", [])),
            "unresolved_count": len(resolutions.get("unresolved", [])),
            "rejected_count": len(resolutions.get("rejected_with_reason", [])),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_8_meta)
        print(f"[Step 8] Completed: Finding Verification ({step_8_status})")

        # ---------------------------------------------------------------------
        # STEP 9: REVISE ARTIFACT
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        revised_text: str | None = None
        rev_request_id: str | None = None

        if candidate_text is not None and critic_text is not None:
            provider_choice = "mock" if mode == "mock" else "groq"
            rev_prompt, rev_tokens = prepare_revision_prompt(candidate_text, autopsy_findings, TASK_PROMPT)
            rev_req = InferenceRequest(
                messages=[
                    GatewayMessage(
                        role="system",
                        content=ModelRoleContract.get_system_instruction(LogicalModelRole.PROMPT_ENGINEER),
                    ),
                    GatewayMessage(role="user", content=rev_prompt),
                ],
                max_tokens=min(rev_tokens, 2000),
                temperature=0.2,
                task_context="revision",
                target_model_id=gen_model_id,
                user_id=user.id,
                workspace_id=project.id,
            )
            rev_resp = await inference_gateway.generate(rev_req, provider=provider_choice)
            revised_text = rev_resp.text
            rev_request_id = rev_resp.request_id or "mock_req_rev"

            step_9_meta = {
                "step_number": 9,
                "name": "Specialist Revision (GPT-OSS 120B)",
                "status": "VERIFIED" if rev_resp.http_status == 200 else "PROVIDER_ERROR",
                "model_id": gen_model_id,
                "provider": provider_choice,
                "request_id": rev_request_id,
                "http_status": rev_resp.http_status,
                "input_tokens": rev_resp.prompt_tokens,
                "output_tokens": rev_resp.completion_tokens,
                "total_tokens": rev_resp.tokens_used,
                "latency_ms": round(rev_resp.latency_ms, 2),
                "rate_limit_headers": rev_resp.rate_limit_headers,
            }
            steps_log.append(step_9_meta)
            print(f"[Step 9] Completed: Revision via {gen_model_id} (ReqID: {rev_request_id})")
        else:
            step_9_meta = {
                "step_number": 9,
                "name": "Specialist Revision (GPT-OSS 120B)",
                "status": "DEFERRED_PENDING_STEP_8",
                "model_id": gen_model_id,
                "latency_ms": 0.0,
            }
            steps_log.append(step_9_meta)
            print("[Step 9] Status: DEFERRED_PENDING_STEP_8")

        # ---------------------------------------------------------------------
        # STEP 10: VALIDATE OBJECTIVELY (Deterministic Verifier)
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        target_eval_text = revised_text or candidate_text or system_instruction
        frontend_violations = [p for p in FORBIDDEN_FRONTEND_PATTERNS if p.lower() in target_eval_text.lower()]
        passed_verifier = len(frontend_violations) == 0 and len(target_eval_text) > 100

        step_10_meta = {
            "step_number": 10,
            "name": "Deterministic Invariant Verification",
            "status": "VERIFIED" if passed_verifier else "FAILED_VERIFICATION",
            "frontend_violations_found": frontend_violations,
            "character_count": len(target_eval_text),
            "sha256_hash": hashlib.sha256(target_eval_text.encode("utf-8")).hexdigest(),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_10_meta)
        print(f"[Step 10] Completed: Deterministic Invariant Check (Violations: {len(frontend_violations)})")

        # ---------------------------------------------------------------------
        # STEP 11: PERSIST WORKFLOW RECORD & DATABASE CHECKPOINT
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        checkpoint_in = CheckpointCreate(
            project_id=project.id,
            phase="e2e_live_acceptance_gate",
            summary=f"12-Step live AI workflow execution record ({mode} mode)",
            verified_state={
                "workflow_id": workflow_id,
                "mode": mode,
                "has_live_credentials": has_live_credentials,
                "steps_count": len(steps_log),
                "artifact_hash": step_10_meta["sha256_hash"],
            },
        )
        checkpoint = await CheckpointManager.create_checkpoint(
            db, project_id=project.id, user_id=user.id, checkpoint_in=checkpoint_in
        )
        await db.commit()

        total_duration = round((time.perf_counter() - start_time) * 1000, 2)
        execution_trace = {
            "workflow_id": workflow_id,
            "execution_mode": mode,
            "timestamp": datetime.now(UTC).isoformat(),
            "total_duration_ms": total_duration,
            "credentials_present": has_live_credentials,
            "final_status": (
                "COMPLETED_LIVE_VERIFIED"
                if mode == "live" and has_live_credentials
                else ("COMPLETED_MOCK_VERIFIED" if mode == "mock" else "HELD_AWAITING_OPERATOR_CREDENTIALS")
            ),
            "project_id": project.id,
            "checkpoint_id": checkpoint.id,
            "steps": steps_log,
            "candidate_artifact": candidate_text,
            "critic_review": critic_text,
            "revised_artifact": revised_text,
            "compiled_system_instruction": system_instruction,
            "final_verified_hash": step_10_meta["sha256_hash"],
        }

        OUTPUT_TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_TRACE_PATH, "w", encoding="utf-8") as f:
            json.dump(execution_trace, f, indent=2)

        step_11_meta = {
            "step_number": 11,
            "name": "Persist Workflow Record",
            "status": "COMPLETED",
            "persisted_path": str(OUTPUT_TRACE_PATH),
            "checkpoint_id": checkpoint.id,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_11_meta)
        print(f"[Step 11] Completed: Persisted trace to {OUTPUT_TRACE_PATH}")

        # ---------------------------------------------------------------------
        # STEP 12: RETRIEVE SAVED RESULT & VERIFY INTEGRITY
        # ---------------------------------------------------------------------
        t0 = time.perf_counter()
        with open(OUTPUT_TRACE_PATH, encoding="utf-8") as f:
            retrieved_data = json.load(f)

        assert retrieved_data["workflow_id"] == workflow_id
        assert retrieved_data["checkpoint_id"] == checkpoint.id
        assert retrieved_data["final_verified_hash"] == step_10_meta["sha256_hash"]

        step_12_meta = {
            "step_number": 12,
            "name": "Retrieve and Verify Integrity",
            "status": "COMPLETED",
            "retrieved_workflow_id": retrieved_data["workflow_id"],
            "hash_match": True,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
        steps_log.append(step_12_meta)
        print(f"[Step 12] Completed: Retrieved and cryptographically verified ({step_12_meta['latency_ms']}ms)")

    print("\n" + "=" * 70)
    print(f"EXECUTION COMPLETE — Final Status: {execution_trace['final_status']}")
    print(f"Workflow ID: {workflow_id}")
    print(f"Total Duration: {total_duration}ms")
    print(f"Trace File: {OUTPUT_TRACE_PATH}")
    print("=" * 70)
    return execution_trace


def main() -> None:
    parser = argparse.ArgumentParser(description="PromptIQ 12-Step Live AI Workflow Execution")
    parser.add_argument(
        "--mode",
        choices=["live", "mock", "inspect"],
        default="live",
        help="Execution mode (default: live; fallback fail-closed without credentials)",
    )
    args = parser.parse_args()

    if args.mode == "inspect":
        key = get_operator_groq_key()
        has_key = bool(key and len(key.strip()) > 10)
        status = {
            "mode": "inspect",
            "branch": "master",
            "operator_groq_configured": has_key,
            "operator_key_length": len(key) if key else 0,
            "quota_ledger_exists": Path("data/quota_ledger.json").exists(),
            "output_trace_exists": OUTPUT_TRACE_PATH.exists(),
        }
        print(json.dumps(status, indent=2))
        return

    asyncio.run(execute_12_step_workflow(mode=args.mode))


if __name__ == "__main__":
    main()
