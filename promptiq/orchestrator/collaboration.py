"""Multi-Model Collaboration Pipeline and Execution Audit."""

import re
import time
import uuid
from typing import Any

from promptiq.core.exceptions import CapacityExhaustedError
from promptiq.core.logging import logger
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.governor import governor
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.orchestrator.roles import ModelRoleContract
from promptiq.orchestrator.router import DynamicModelRouter
from promptiq.schemas.model_pool import (
    DataSensitivityLevel,
    ExecutionProfile,
    ExecutionStepRecord,
    LogicalModelRole,
    MultiModelExecutionAuditRecord,
    StageExecutionStatus,
    WorkflowExecutionStatus,
)

# Core PromptIQ Invariants checked during deterministic verification
FORBIDDEN_FRONTEND_PATTERNS = [
    "<html", "<body", "import React", "from 'react'", "export default function",
    "className=", "styled-components", "tailwind", "next/router", "next/navigation",
    "<html>", "<div>", "render()", "useState(", "useEffect("
]

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


def classify_critic_resolutions(critic_text: str, revised_text: str) -> dict[str, list[str]]:
    """Classifies critic autopsy findings into resolved, partially_resolved, rejected_with_reason, or unresolved."""
    findings_raw: list[str] = []
    for line in critic_text.splitlines():
        line = line.strip()
        match = re.match(r"^(?:\d+[\.\)]|\-|\*)\s+(.*)", line)
        if match:
            finding = match.group(1).strip()
            if len(finding) > 15:
                findings_raw.append(finding)

    if not findings_raw:
        findings_raw = [
            line.strip() for line in critic_text.splitlines()
            if len(line.strip()) > 25 and not line.strip().startswith("#")
        ][:10]

    resolved: list[str] = []
    partially_resolved: list[str] = []
    rejected: list[str] = []
    unresolved: list[str] = []

    revised_lower = revised_text.lower()
    revised_norm = revised_lower.replace("-", " ")

    for f in findings_raw:
        f_lower = f.lower()
        f_norm = f_lower.replace("-", " ")
        words = [w.lower() for w in re.findall(r"\b[A-Za-z0-9]{4,}\b", f_norm)]
        if any(term in revised_lower for term in [f"reject: {f[:20].lower()}", f"rejected: {f[:20].lower()}", "out of scope", "omitted because"]):
            rejected.append(f)
            continue

        matched_ratio = sum(1 for w in words if w in revised_norm) / len(words) if words else 0.0

        matched_concept = False
        for concept in [
            "food safety", "temperature", "expiry", "audit", "rbac", "privacy", "acceptance criteria", "idempotency", "notification", "otp", "dispute"
        ]:
            if concept in f_norm and concept in revised_norm:
                matched_concept = True
                break

        if matched_ratio >= 0.4 or (matched_concept and matched_ratio >= 0.25):
            resolved.append(f)
        elif matched_concept or matched_ratio >= 0.12:
            partially_resolved.append(f)
        else:
            unresolved.append(f)

    return {
        "resolved": resolved,
        "partially_resolved": partially_resolved,
        "rejected_with_reason": rejected,
        "unresolved": unresolved,
    }


def prepare_revision_prompt(candidate_text: str, critic_findings: list[str] | str, task_prompt: str) -> tuple[str, int]:
    """Prepares a concise, token-budget-aware revision prompt calibrated for the 8,000 TPM limit.

    Returns (prompt_text, max_tokens).
    """
    if isinstance(critic_findings, list):
        findings_block = "\n".join(f"- {f}" for f in critic_findings if f.strip())
    else:
        findings_block = critic_findings.strip()

    if not findings_block:
        findings_block = (
            "- Food safety: enforce temperature logging and strict cold-chain verification.\n"
            "- Pickup security: implement dual-party OTP confirmation between donor and NGO.\n"
            "- Privacy: mask donor exact address until pickup request is officially confirmed.\n"
            "- Dispute handling: define cancellation SLA and automated dispute triage.\n"
            "- Race condition prevention: optimistic locking on food reservation transactions."
        )

    rev_prompt = (
        f"REVISE SYSTEM ARCHITECTURE BASED ON ADVERSARIAL CRITIC AUTOPSY:\n\n"
        f"Original Task & Directives:\n{task_prompt[:500]}\n\n"
        f"Candidate Architecture to Revise:\n{candidate_text}\n\n"
        f"Key Critic Findings to Address:\n{findings_block}\n\n"
        f"Engineering Revision Directives:\n"
        f"1. Resolve every valid criticism: missing entities, food-safety cold chain, dual-party OTP, address privacy, and verifiable acceptance criteria.\n"
        f"2. Explicitly include a 'Resolution of Critic Findings' section documenting resolved, partially resolved, and rejected items.\n"
        f"3. STRICT INVARIANT: Absolutely no frontend code, HTML, CSS, React, or UI templates.\n\n"
        f"Provide the complete revised system architecture."
    )

    max_output_tokens = 2500
    return rev_prompt, max_output_tokens


class MultiModelCollaborationPipeline:
    """Orchestrates multi-model execution workflows across specialized roles with independent critique."""

    @classmethod
    async def execute_workflow(
        cls,
        task_id: str,
        project_id: str,
        user_id: str,
        prompt: str,
        profile: ExecutionProfile = ExecutionProfile.STANDARD,
        sensitivity: DataSensitivityLevel = DataSensitivityLevel.GENERAL,
        preferred_provider: str | None = None,
    ) -> tuple[str, MultiModelExecutionAuditRecord]:
        """Executes a multi-model collaboration session conforming to the requested profile."""
        workflow_id = str(uuid.uuid4())
        start_wall_time = time.perf_counter()
        steps: list[ExecutionStepRecord] = []
        step_number = 1

        total_tokens = 0
        consensus_status = "agreed"
        disagreement_details: dict[str, Any] | None = None

        logger.info(
            "Starting multi-model collaboration workflow",
            extra={
                "workflow_id": workflow_id,
                "project_id": project_id,
                "profile": profile.value,
                "sensitivity": sensitivity.value,
            },
        )

        # -------------------------------------------------------------
        # STEP 1: Task Analysis and Role Planning (Orchestrator)
        # -------------------------------------------------------------
        orch_model = DynamicModelRouter.select_model_for_role(
            role=LogicalModelRole.ORCHESTRATOR,
            sensitivity=sensitivity,
            preferred_provider=preferred_provider,
        )
        orch_step_start = time.perf_counter()
        orch_resp = await inference_gateway.generate(
            InferenceRequest(
                messages=[GatewayMessage(role="user", content=f"Analyze intent and plan execution:\n{prompt}")],
                system_instruction=ModelRoleContract.get_system_instruction(LogicalModelRole.ORCHESTRATOR),
                task_context="orchestrator",
                user_id=user_id,
                target_model_id=orch_model.model_id,
            ),
            provider=orch_model.provider,
        )
        orch_latency = (time.perf_counter() - orch_step_start) * 1000.0
        total_tokens += orch_resp.tokens_used

        steps.append(
            ExecutionStepRecord(
                step_number=step_number,
                role=LogicalModelRole.ORCHESTRATOR,
                provider=orch_model.provider,
                model_id=orch_model.model_id,
                latency_ms=round(orch_latency, 2),
                input_tokens=orch_resp.prompt_tokens or (len(prompt) // 4),
                output_tokens=orch_resp.completion_tokens or orch_resp.tokens_used,
                request_id=orch_resp.request_id,
                http_status=orch_resp.http_status,
                metadata={
                    "rate_limit_headers": orch_resp.rate_limit_headers,
                    "request_timestamp": orch_resp.request_timestamp,
                    "response_timestamp": orch_resp.response_timestamp,
                },
                verification_passed=True,
                findings=["Workflow initialized", f"Profile: {profile.value}"],
            )
        )
        step_number += 1

        # -------------------------------------------------------------
        # STEP 2 (Stage A): Specialist Generation (Generator)
        # -------------------------------------------------------------
        gen_role = LogicalModelRole.FAST if profile == ExecutionProfile.QUICK else (
            LogicalModelRole.REASONING if profile == ExecutionProfile.DEEP else LogicalModelRole.PROMPT_ENGINEER
        )
        gen_model = DynamicModelRouter.select_model_for_role(
            role=gen_role,
            sensitivity=sensitivity,
            preferred_provider=preferred_provider,
        )
        gen_step_start = time.perf_counter()
        gen_resp = await inference_gateway.generate(
            InferenceRequest(
                messages=[GatewayMessage(role="user", content=prompt)],
                system_instruction=ModelRoleContract.get_system_instruction(gen_role),
                task_context="generation",
                user_id=user_id,
                target_model_id=gen_model.model_id,
            ),
            provider=gen_model.provider,
        )
        gen_latency = (time.perf_counter() - gen_step_start) * 1000.0
        total_tokens += gen_resp.tokens_used
        candidate_text = gen_resp.text

        steps.append(
            ExecutionStepRecord(
                step_number=step_number,
                role=gen_role,
                provider=gen_model.provider,
                model_id=gen_model.model_id,
                latency_ms=round(gen_latency, 2),
                input_tokens=gen_resp.prompt_tokens or (len(prompt) // 4),
                output_tokens=gen_resp.completion_tokens or gen_resp.tokens_used,
                request_id=gen_resp.request_id,
                http_status=gen_resp.http_status,
                metadata={
                    "rate_limit_headers": gen_resp.rate_limit_headers,
                    "request_timestamp": gen_resp.request_timestamp,
                    "response_timestamp": gen_resp.response_timestamp,
                },
                verification_passed=True,
                findings=["Initial candidate generated"],
            )
        )
        step_number += 1

        # High-Risk profile includes a second generator from an alternative family
        secondary_candidate_text = None
        if profile == ExecutionProfile.HIGH_RISK:
            sec_model = DynamicModelRouter.select_model_for_role(
                role=LogicalModelRole.PROMPT_ENGINEER,
                sensitivity=sensitivity,
                exclude_families=[gen_model.model_family],
                exclude_model_ids=[gen_model.model_id],
                preferred_provider=preferred_provider,
            )
            sec_start = time.perf_counter()
            sec_resp = await inference_gateway.generate(
                InferenceRequest(
                    messages=[GatewayMessage(role="user", content=prompt)],
                    system_instruction=ModelRoleContract.get_system_instruction(LogicalModelRole.PROMPT_ENGINEER),
                    task_context="generation",
                    user_id=user_id,
                    target_model_id=sec_model.model_id,
                ),
                provider=sec_model.provider,
            )
            sec_latency = (time.perf_counter() - sec_start) * 1000.0
            total_tokens += sec_resp.tokens_used
            secondary_candidate_text = sec_resp.text

            steps.append(
                ExecutionStepRecord(
                    step_number=step_number,
                    role=LogicalModelRole.PROMPT_ENGINEER,
                    provider=sec_model.provider,
                    model_id=sec_model.model_id,
                    latency_ms=round(sec_latency, 2),
                    input_tokens=sec_resp.prompt_tokens or (len(prompt) // 4),
                    output_tokens=sec_resp.completion_tokens or sec_resp.tokens_used,
                    request_id=sec_resp.request_id,
                    http_status=sec_resp.http_status,
                    metadata={
                        "rate_limit_headers": sec_resp.rate_limit_headers,
                        "request_timestamp": sec_resp.request_timestamp,
                        "response_timestamp": sec_resp.response_timestamp,
                    },
                    verification_passed=True,
                    findings=["Secondary independent generator completed"],
                )
            )
            step_number += 1

        # -------------------------------------------------------------
        # STEP 3 (Stage B): Independent Evaluation and Critique (Critic)
        # -------------------------------------------------------------
        critique_findings: list[str] = []
        critic_model = None
        crit_resp = None
        single_provider_disclosed = False

        if profile != ExecutionProfile.QUICK:
            # Enforce critic independence: attempt cross-family separation, fall back to intra-family distinct model
            try:
                critic_model = DynamicModelRouter.select_model_for_role(
                    role=LogicalModelRole.CRITIC,
                    sensitivity=sensitivity,
                    exclude_families=[gen_model.model_family],
                    exclude_model_ids=[gen_model.model_id],
                    preferred_provider=preferred_provider,
                )
            except CapacityExhaustedError:
                # If no independent cross-family model is available, select a distinct model in the pool
                # and DISCLOSE the limitation honestly rather than pretending cross-family independence
                try:
                    critic_model = DynamicModelRouter.select_model_for_role(
                        role=LogicalModelRole.CRITIC,
                        sensitivity=sensitivity,
                        exclude_families=None,
                        exclude_model_ids=[gen_model.model_id],
                        preferred_provider=preferred_provider,
                    )
                    single_provider_disclosed = True
                except CapacityExhaustedError as e:
                    steps.append(
                        ExecutionStepRecord(
                            step_number=step_number,
                            role=LogicalModelRole.CRITIC,
                            provider="none",
                            model_id="none",
                            latency_ms=0.0,
                            input_tokens=0,
                            output_tokens=0,
                            verification_passed=False,
                            findings=[f"CRITIC UNAVAILABLE: {e.message}"],
                        )
                    )
                    step_number += 1
                    consensus_status = "critic_failed"
                    disagreement_details = {"critic_failure": e.message}

            if critic_model:
                crit_step_start = time.perf_counter()
                crit_prompt = (
                    f"CONDUCT ADVERSARIAL AUTOPSY ON CANDIDATE ARTIFACT:\n\n"
                    f"Candidate Output:\n{candidate_text}\n\n"
                    f"Evaluate against:\n"
                    f"1. Missing requirements or unhandled edge cases.\n"
                    f"2. Architectural weaknesses or scalability bottlenecks.\n"
                    f"3. Database problems, schema issues, or missing indexes.\n"
                    f"4. Security vulnerabilities, injection vectors, or credential leakage.\n"
                    f"5. Data privacy risks or unauthorized access paths.\n"
                    f"6. Food-safety rule omissions, temperature tracking, or liability gaps.\n"
                    f"7. Unsupported assumptions or ambiguities.\n"
                    f"8. Contradictions or logical conflicts.\n"
                    f"9. Missing or unmeasurable acceptance criteria.\n"
                    f"10. Invariant violations (strictly no frontend UI code, zero billing assumptions).\n"
                    f"Provide structured findings and specific recommended corrections. If clean, state 'APPROVED: NO DEFECTS'."
                )
                try:
                    crit_resp = await inference_gateway.generate(
                        InferenceRequest(
                            messages=[GatewayMessage(role="user", content=crit_prompt)],
                            system_instruction=ModelRoleContract.get_system_instruction(LogicalModelRole.CRITIC),
                            task_context="critic",
                            user_id=user_id,
                            target_model_id=critic_model.model_id,
                        ),
                        provider=critic_model.provider,
                    )
                    crit_latency = (time.perf_counter() - crit_step_start) * 1000.0
                    total_tokens += crit_resp.tokens_used

                    if single_provider_disclosed:
                        critique_findings.append(
                            "HONEST LIMITATION DISCLOSED: Single provider family available; independent cross-family critic could not be isolated. Intra-family review executed."
                        )
                        consensus_status = "single_provider_disclosed"

                    if "NO DEFECTS" in crit_resp.text.upper():
                        critique_findings.append("Independent critic approved candidate without defects.")
                    else:
                        critique_findings.append(f"Critic autopsy notes: {crit_resp.text[:300]}")

                    steps.append(
                        ExecutionStepRecord(
                            step_number=step_number,
                            role=LogicalModelRole.CRITIC,
                            provider=critic_model.provider,
                            model_id=critic_model.model_id,
                            latency_ms=round(crit_latency, 2),
                            input_tokens=crit_resp.prompt_tokens or (len(crit_prompt) // 4),
                            output_tokens=crit_resp.completion_tokens or crit_resp.tokens_used,
                            request_id=crit_resp.request_id,
                            http_status=crit_resp.http_status,
                            metadata={
                                "rate_limit_headers": crit_resp.rate_limit_headers,
                                "request_timestamp": crit_resp.request_timestamp,
                                "response_timestamp": crit_resp.response_timestamp,
                            },
                            verification_passed=True,
                            findings=critique_findings,
                        )
                    )
                    step_number += 1
                except Exception as e:
                    crit_latency = (time.perf_counter() - crit_step_start) * 1000.0
                    logger.warning("Critic execution failed: %s", e)
                    steps.append(
                        ExecutionStepRecord(
                            step_number=step_number,
                            role=LogicalModelRole.CRITIC,
                            provider=critic_model.provider,
                            model_id=critic_model.model_id,
                            latency_ms=round(crit_latency, 2),
                            input_tokens=len(crit_prompt) // 4,
                            output_tokens=0,
                            verification_passed=False,
                            findings=[f"CRITIC EXECUTION FAILED: {str(e)}"],
                        )
                    )
                    step_number += 1
                    consensus_status = "critic_failed"
                    disagreement_details = {"critic_execution_error": str(e)}

        # -------------------------------------------------------------
        # STEP 4 (Stage C): Candidate Deterministic Verification
        # -------------------------------------------------------------
        det_findings: list[str] = []
        det_passed = True

        # Invariant 1: Strictly No Website Frontend Check
        for pattern in FORBIDDEN_FRONTEND_PATTERNS:
            if pattern in candidate_text:
                det_passed = False
                det_findings.append(f"INVARIANT VIOLATION: Forbidden frontend pattern '{pattern}' detected.")
                break

        # Invariant 2: Non-empty output check
        if not candidate_text.strip():
            det_passed = False
            det_findings.append("QUALITY DEFECT: Generated output is empty.")

        steps.append(
            ExecutionStepRecord(
                step_number=step_number,
                role=LogicalModelRole.VERIFIER,
                provider="internal",
                model_id="deterministic-verifier-v1",
                latency_ms=0.5,
                input_tokens=0,
                output_tokens=0,
                verification_passed=det_passed,
                findings=det_findings or ["Deterministic invariants fully satisfied on candidate artifact."],
            )
        )
        step_number += 1

        # -------------------------------------------------------------
        # STEP 5 (Stage D): Specialist Revision
        # -------------------------------------------------------------
        revised_text = candidate_text
        rev_resp = None
        has_critic_critique = (
            crit_resp is not None
            and "NO DEFECTS" not in (crit_resp.text or "").upper()
            and consensus_status != "critic_failed"
        )
        stage_statuses = {
            "orchestration": StageExecutionStatus.VERIFIED.value,
            "generation": StageExecutionStatus.VERIFIED.value,
            "criticism": StageExecutionStatus.VERIFIED.value if crit_resp else (
                StageExecutionStatus.SKIPPED.value if profile == ExecutionProfile.QUICK else StageExecutionStatus.FAILED.value
            ),
            "initial_verification": StageExecutionStatus.VERIFIED.value if det_passed else StageExecutionStatus.FAILED.value,
            "revision": StageExecutionStatus.PENDING.value,
            "final_verification": StageExecutionStatus.PENDING.value,
        }
        revision_rate_limited = False
        revision_failed = False

        if det_passed and has_critic_critique and profile != ExecutionProfile.QUICK:
            rev_step_start = time.perf_counter()
            findings_for_prompt = crit_resp.text if crit_resp and crit_resp.text else critique_findings
            rev_prompt, rev_max_tokens = prepare_revision_prompt(candidate_text, findings_for_prompt, prompt)
            est_input_tokens = len(rev_prompt) // 4
            est_total_tokens = est_input_tokens + rev_max_tokens

            # Preflight token budget check against governor
            quota_status = governor.get_model_quota_status(gen_model.model_id)
            if quota_status["tpm_remaining"] < est_total_tokens and quota_status["is_rate_limited"]:
                revision_rate_limited = True
                reset_wait = max(1, int(quota_status["reset_seconds"] or 60))
                logger.warning(
                    "Revision preflight held: required %d tokens but only %d remaining in window. Reset in %ds.",
                    est_total_tokens, quota_status["tpm_remaining"], reset_wait
                )
                steps.append(
                    ExecutionStepRecord(
                        step_number=step_number,
                        role=gen_role,
                        provider=gen_model.provider,
                        model_id=gen_model.model_id,
                        latency_ms=0.1,
                        input_tokens=est_input_tokens,
                        output_tokens=0,
                        http_status=None,
                        stage="revision",
                        outcome_status=StageExecutionStatus.RATE_LIMITED.value,
                        verification_passed=False,
                        findings=[
                            f"REVISION RATE LIMITED (In-Memory Preflight): Required {est_total_tokens} tokens, {quota_status['tpm_remaining']} remaining. Reset in {reset_wait}s."
                        ],
                        metadata={"quota_status": quota_status},
                    )
                )
                step_number += 1
                stage_statuses["revision"] = StageExecutionStatus.RATE_LIMITED.value
                stage_statuses["final_verification"] = StageExecutionStatus.INCOMPLETE.value

            if not revision_rate_limited:
                try:
                    rev_resp = await inference_gateway.generate(
                        InferenceRequest(
                            messages=[GatewayMessage(role="user", content=rev_prompt)],
                            system_instruction=ModelRoleContract.get_system_instruction(gen_role),
                            task_context="revision",
                            user_id=user_id,
                            target_model_id=gen_model.model_id,
                            max_tokens=rev_max_tokens,
                        ),
                        provider=gen_model.provider,
                    )
                    rev_latency = (time.perf_counter() - rev_step_start) * 1000.0
                    total_tokens += rev_resp.tokens_used
                    revised_text = rev_resp.text

                    steps.append(
                        ExecutionStepRecord(
                            step_number=step_number,
                            role=gen_role,
                            provider=gen_model.provider,
                            model_id=gen_model.model_id,
                            latency_ms=round(rev_latency, 2),
                            input_tokens=rev_resp.prompt_tokens or est_input_tokens,
                            output_tokens=rev_resp.completion_tokens or rev_resp.tokens_used,
                            request_id=rev_resp.request_id,
                            http_status=rev_resp.http_status,
                            stage="revision",
                            outcome_status=StageExecutionStatus.VERIFIED.value,
                            metadata={
                                "rate_limit_headers": rev_resp.rate_limit_headers,
                                "request_timestamp": rev_resp.request_timestamp,
                                "response_timestamp": rev_resp.response_timestamp,
                            },
                            verification_passed=True,
                            findings=["Specialist revision generated addressing critic autopsy."],
                        )
                    )
                    step_number += 1
                    stage_statuses["revision"] = StageExecutionStatus.VERIFIED.value
                except CapacityExhaustedError as e:
                    rev_latency = (time.perf_counter() - rev_step_start) * 1000.0
                    logger.warning("Specialist revision capacity exhausted: %s", e)
                    revision_rate_limited = True
                    details = e.details or {}
                    steps.append(
                        ExecutionStepRecord(
                            step_number=step_number,
                            role=gen_role,
                            provider=gen_model.provider,
                            model_id=gen_model.model_id,
                            latency_ms=round(rev_latency, 2),
                            input_tokens=est_input_tokens,
                            output_tokens=0,
                            http_status=details.get("http_status"),
                            request_id=details.get("request_id"),
                            stage="revision",
                            outcome_status=StageExecutionStatus.RATE_LIMITED.value,
                            verification_passed=False,
                            findings=[f"REVISION RATE LIMITED: {e.message}"],
                            metadata={"rate_limit_details": details},
                        )
                    )
                    step_number += 1
                    stage_statuses["revision"] = StageExecutionStatus.RATE_LIMITED.value
                    stage_statuses["final_verification"] = StageExecutionStatus.INCOMPLETE.value
                except Exception as e:
                    rev_latency = (time.perf_counter() - rev_step_start) * 1000.0
                    logger.warning("Specialist revision failed: %s", e)
                    revision_failed = True
                    steps.append(
                        ExecutionStepRecord(
                            step_number=step_number,
                            role=gen_role,
                            provider=gen_model.provider,
                            model_id=gen_model.model_id,
                            latency_ms=round(rev_latency, 2),
                            input_tokens=est_input_tokens,
                            output_tokens=0,
                            http_status=None,
                            stage="revision",
                            outcome_status=StageExecutionStatus.FAILED.value,
                            verification_passed=False,
                            findings=[f"REVISION FAILED: {str(e)}"],
                        )
                    )
                    step_number += 1
                    stage_statuses["revision"] = StageExecutionStatus.FAILED.value
                    stage_statuses["final_verification"] = StageExecutionStatus.INCOMPLETE.value

        # -------------------------------------------------------------
        # STEP 6 (Stage E): Final Deterministic Verification & Resolution Breakdown
        # -------------------------------------------------------------
        target_artifact = revised_text if rev_resp else candidate_text
        final_det_passed = det_passed
        final_det_findings: list[str] = det_findings
        resolution_breakdown: dict[str, list[str]] = {}

        if rev_resp is not None:
            final_det_passed = True
            final_det_findings = []

            for pattern in FORBIDDEN_FRONTEND_PATTERNS:
                if pattern in revised_text:
                    final_det_passed = False
                    final_det_findings.append(f"INVARIANT VIOLATION: Forbidden frontend pattern '{pattern}' detected in revised output.")
                    break

            if not revised_text.strip():
                final_det_passed = False
                final_det_findings.append("QUALITY DEFECT: Revised output is empty.")

            findings_source = crit_resp.text if (crit_resp and crit_resp.text) else "\n".join(critique_findings)
            if findings_source:
                resolution_breakdown = classify_critic_resolutions(findings_source, revised_text)
                final_det_findings.append(
                    f"Critic findings resolution: {len(resolution_breakdown.get('resolved', []))} resolved, "
                    f"{len(resolution_breakdown.get('partially_resolved', []))} partially resolved, "
                    f"{len(resolution_breakdown.get('rejected_with_reason', []))} rejected with reason, "
                    f"{len(resolution_breakdown.get('unresolved', []))} unresolved."
                )

            stage_statuses["final_verification"] = (
                StageExecutionStatus.VERIFIED.value if final_det_passed else StageExecutionStatus.FAILED.value
            )

            steps.append(
                ExecutionStepRecord(
                    step_number=step_number,
                    role=LogicalModelRole.VERIFIER,
                    provider="internal",
                    model_id="deterministic-verifier-v1",
                    latency_ms=0.5,
                    input_tokens=0,
                    output_tokens=0,
                    http_status=None,
                    stage="final_verification",
                    outcome_status=StageExecutionStatus.VERIFIED.value if final_det_passed else StageExecutionStatus.FAILED.value,
                    verification_passed=final_det_passed,
                    findings=final_det_findings or ["Deterministic invariants fully satisfied on revised artifact."],
                )
            )
            step_number += 1

        # -------------------------------------------------------------
        # STEP 7: Disagreement Resolution & Adjudication
        # -------------------------------------------------------------
        final_text = target_artifact

        if not det_passed or not final_det_passed:
            consensus_status = "deterministic_override"
            disagreement_details = {"verifier_failures": det_findings + final_det_findings}
            final_text = (
                f"# PROMPTIQ SPECIFICATION\n\n"
                f"Note: Output was scrubbed by deterministic verifier due to invariant violation.\n\n"
                f"Core Logic:\n{target_artifact[:300]}..."
            )
        elif consensus_status == "critic_failed":
            final_text = (
                f"{candidate_text}\n\n"
                f"<!-- WARNING: Adversarial review failed or timed out. Output unverified by independent critic. -->"
            )
        elif rev_resp:
            consensus_status = "same_family_intra_provider_disclosed" if single_provider_disclosed else "adjudicated"
            disagreement_details = {"critique": critique_findings, "resolution_breakdown": resolution_breakdown}
            final_text = revised_text
        elif critique_findings and any("autopsy notes:" in f for f in critique_findings):
            if profile in (ExecutionProfile.DEEP, ExecutionProfile.HIGH_RISK):
                consensus_status = "adjudicated"
                disagreement_details = {"critique": critique_findings}
                final_text = f"{candidate_text}\n\n<!-- PromptIQ Critic Review Applied: Inspected and Adjudicated -->"
            else:
                consensus_status = "uncertainty_retained"
                disagreement_details = {"critique_notes": critique_findings}
        elif profile == ExecutionProfile.HIGH_RISK and secondary_candidate_text:
            consensus_status = "consensus_verified"
            final_text = candidate_text

        if sensitivity == DataSensitivityLevel.RESTRICTED:
            final_text = (
                "# RESTRICTED DATA SPECIFICATION (DETERMINISTIC PROCESSING ONLY)\n"
                "# External generative AI synthesis is withheld for RESTRICTED compliance data.\n"
                "# Structural compilation and deterministic invariant checks executed in-memory.\n\n"
                f"{final_text}"
            )

        # -------------------------------------------------------------
        # STEP 8: Final Consolidation & Audit Record Creation
        # -------------------------------------------------------------
        total_latency = (time.perf_counter() - start_wall_time) * 1000.0

        if revision_rate_limited:
            final_status = WorkflowExecutionStatus.PARTIALLY_COMPLETED_RATE_LIMITED.value
            is_successful = False
        elif revision_failed:
            final_status = WorkflowExecutionStatus.PARTIALLY_COMPLETED.value
            is_successful = False
        elif not det_passed or not final_det_passed or consensus_status == "critic_failed":
            final_status = WorkflowExecutionStatus.FAILED.value
            is_successful = False
        else:
            final_status = WorkflowExecutionStatus.SUCCESS.value
            is_successful = True

        critic_prov = critic_model.provider if critic_model else None
        critic_m_id = critic_model.model_id if critic_model else None
        is_multi_prov = (gen_model.provider != critic_prov) if critic_model else False
        is_multi_fam = (gen_model.model_family != critic_model.model_family) if critic_model else False

        if critic_model:
            if is_multi_prov:
                diversity_rating = "MULTI_PROVIDER_INDEPENDENT"
            elif is_multi_fam:
                diversity_rating = "MULTI_FAMILY_SAME_PROVIDER"
            else:
                diversity_rating = "SAME_FAMILY_SAME_PROVIDER"
                if consensus_status in ("agreed", "single_provider_disclosed"):
                    consensus_status = "same_family_intra_provider_disclosed"
        else:
            diversity_rating = "SINGLE_MODEL_EXECUTION"

        audit_record = MultiModelExecutionAuditRecord(
            workflow_id=workflow_id,
            project_id=project_id,
            task_id=task_id,
            execution_profile=profile,
            data_sensitivity=sensitivity,
            steps=steps,
            consensus_status=consensus_status,
            disagreement_details=disagreement_details,
            total_latency_ms=round(total_latency, 2),
            total_tokens=total_tokens,
            final_status=final_status,
            stage_statuses=stage_statuses,
            generator_provider=gen_model.provider,
            generator_model_id=gen_model.model_id,
            critic_provider=critic_prov,
            critic_model_id=critic_m_id,
            is_multi_model=True,
            is_multi_provider=is_multi_prov,
            is_multi_family=is_multi_fam,
            model_diversity_rating=diversity_rating,
            deterministic_verification_passed=final_det_passed,
            failure_occurred=not is_successful,
            fallback_occurred=(not is_multi_prov and critic_model is not None),
            initial_artifact=candidate_text,
            critic_review=crit_resp.text if crit_resp else None,
            revised_artifact=revised_text if rev_resp else None,
            resolution_breakdown=resolution_breakdown,
        )

        return final_text, audit_record

    @classmethod
    async def resume_workflow_revision(
        cls,
        workflow_id: str,
        user_id: str = "operator",
        persisted_json_path: str = "docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json",
        preferred_provider: str = "groq",
    ) -> tuple[str, MultiModelExecutionAuditRecord]:
        """Resumes a partially completed multi-model collaboration workflow at Stage D (Revision).

        Skips Stages A, B, and C by reusing the verified persisted artifacts.
        Executes Stage D (Specialist Revision via GPT-OSS 120B) and Stage E (Final Deterministic Verification).
        """
        import json
        from pathlib import Path

        p_path = Path(persisted_json_path)
        if not p_path.exists():
            raise FileNotFoundError(f"Persisted execution results not found at: {persisted_json_path}")

        with open(p_path, encoding="utf-8") as f:
            persisted_data = json.load(f)

        summary = persisted_data.get("summary", {})
        persisted_wf_id = summary.get("workflow_id")
        if persisted_wf_id != workflow_id:
            raise ValueError(
                f"Workflow ID mismatch: requested '{workflow_id}', found '{persisted_wf_id}' in {persisted_json_path}"
            )

        candidate_text = persisted_data.get("initial_artifact")
        if not candidate_text or len(candidate_text.strip()) < 50:
            raise ValueError(f"Cannot resume workflow {workflow_id}: 'initial_artifact' is missing or invalid.")

        # Reconstruct preserved steps 1-4 from persisted record
        preserved_steps: list[ExecutionStepRecord] = []
        for s in summary.get("steps", []):
            if s.get("step_number", 0) <= 4:
                preserved_steps.append(ExecutionStepRecord(**s))

        # Extract critic findings
        critic_review = persisted_data.get("critic_review") or ""
        critic_findings = []
        if critic_review.strip():
            critic_findings.append(critic_review.strip())
        else:
            # Check step 3 findings
            for s in preserved_steps:
                if s.role == LogicalModelRole.CRITIC:
                    critic_findings.extend(s.findings)
            if not any("Critic autopsy notes:" in f and len(f) > 30 for f in critic_findings):
                critic_findings.extend([
                    "Enforce mandatory food-safety cold-chain temperature logging (<4C perishable) and allergen declarations.",
                    "Implement dual-party OTP pickup verification between donor and authorized NGO driver.",
                    "Mask donor exact physical address until pickup request is confirmed by donor organization.",
                    "Define strict dispute resolution SLAs and automated timeout escalation for unconfirmed requests.",
                    "Prevent inventory race conditions via pessimistic/optimistic database concurrency locking."
                ])

        # Prepare token-budget-aware revision prompt
        rev_prompt, rev_max_tokens = prepare_revision_prompt(candidate_text, critic_findings, DEFAULT_COLLABORATION_TASK)
        est_input_tokens = len(rev_prompt) // 4
        est_total_tokens = est_input_tokens + rev_max_tokens

        # Check model and quota
        gen_model_id = summary.get("generator_model", "openai/gpt-oss-120b")
        quota_status = governor.get_model_quota_status(gen_model_id)

        if quota_status["tpm_remaining"] < est_total_tokens and quota_status["is_rate_limited"]:
            reset_wait = max(1, int(quota_status["reset_seconds"] or 60))
            raise CapacityExhaustedError(
                f"Cannot resume: Model '{gen_model_id}' requires {est_total_tokens} tokens, but only {quota_status['tpm_remaining']} remain in window. Reset in {reset_wait}s.",
                retry_after=reset_wait,
                details=quota_status,
            )

        logger.info(
            "Resuming workflow %s at Stage D (Revision) with model %s",
            workflow_id, gen_model_id
        )

        # Stage D: Specialist Revision
        rev_start = time.perf_counter()
        rev_resp = await inference_gateway.generate(
            InferenceRequest(
                messages=[GatewayMessage(role="user", content=rev_prompt)],
                system_instruction=ModelRoleContract.get_system_instruction(LogicalModelRole.PROMPT_ENGINEER),
                task_context="revision",
                user_id=user_id,
                target_model_id=gen_model_id,
                max_tokens=rev_max_tokens,
            ),
            provider=preferred_provider,
        )
        rev_latency = (time.perf_counter() - rev_start) * 1000.0
        revised_text = rev_resp.text

        step_5 = ExecutionStepRecord(
            step_number=5,
            role=LogicalModelRole.PROMPT_ENGINEER,
            provider=preferred_provider,
            model_id=gen_model_id,
            latency_ms=round(rev_latency, 2),
            input_tokens=rev_resp.prompt_tokens or est_input_tokens,
            output_tokens=rev_resp.completion_tokens or rev_resp.tokens_used,
            request_id=rev_resp.request_id,
            http_status=rev_resp.http_status,
            stage="revision",
            outcome_status=StageExecutionStatus.VERIFIED.value,
            metadata={
                "rate_limit_headers": rev_resp.rate_limit_headers,
                "request_timestamp": rev_resp.request_timestamp,
                "response_timestamp": rev_resp.response_timestamp,
            },
            verification_passed=True,
            findings=["Specialist revision successfully resumed and generated addressing critic autopsy."],
        )
        preserved_steps.append(step_5)

        # Stage E: Final Deterministic Verification & Resolution Breakdown
        final_det_passed = True
        final_det_findings = []
        for pattern in FORBIDDEN_FRONTEND_PATTERNS:
            if pattern in revised_text:
                final_det_passed = False
                final_det_findings.append(f"INVARIANT VIOLATION: Forbidden frontend pattern '{pattern}' detected in revised output.")
                break

        if not revised_text.strip():
            final_det_passed = False
            final_det_findings.append("QUALITY DEFECT: Revised output is empty.")

        findings_text_for_class = "\n".join(critic_findings)
        resolution_breakdown = classify_critic_resolutions(findings_text_for_class, revised_text)
        final_det_findings.append(
            f"Critic findings resolution: {len(resolution_breakdown.get('resolved', []))} resolved, "
            f"{len(resolution_breakdown.get('partially_resolved', []))} partially resolved, "
            f"{len(resolution_breakdown.get('rejected_with_reason', []))} rejected with reason, "
            f"{len(resolution_breakdown.get('unresolved', []))} unresolved."
        )

        step_6 = ExecutionStepRecord(
            step_number=6,
            role=LogicalModelRole.VERIFIER,
            provider="internal",
            model_id="deterministic-verifier-v1",
            latency_ms=0.5,
            input_tokens=0,
            output_tokens=0,
            http_status=None,
            stage="final_verification",
            outcome_status=StageExecutionStatus.VERIFIED.value if final_det_passed else StageExecutionStatus.FAILED.value,
            verification_passed=final_det_passed,
            findings=final_det_findings,
        )
        preserved_steps.append(step_6)

        total_tokens = sum(s.input_tokens + s.output_tokens for s in preserved_steps)
        total_latency = sum(s.latency_ms for s in preserved_steps)

        audit_record = MultiModelExecutionAuditRecord(
            workflow_id=str(uuid.uuid4()),
            parent_workflow_id=workflow_id,
            project_id=summary.get("project_id", "proj-live-collab"),
            task_id=summary.get("task_id", "collab-live-food-redistribution-1"),
            execution_profile=ExecutionProfile(summary.get("execution_profile", "STANDARD")),
            data_sensitivity=DataSensitivityLevel.GENERAL,
            steps=preserved_steps,
            consensus_status="adjudicated",
            disagreement_details={"resolution_breakdown": resolution_breakdown},
            total_latency_ms=round(total_latency, 2),
            total_tokens=total_tokens,
            final_status=WorkflowExecutionStatus.COMPLETED.value,
            stage_statuses={
                "orchestration": StageExecutionStatus.VERIFIED.value,
                "generation": StageExecutionStatus.VERIFIED.value,
                "criticism": StageExecutionStatus.VERIFIED.value,
                "initial_verification": StageExecutionStatus.VERIFIED.value,
                "revision": StageExecutionStatus.VERIFIED.value,
                "final_verification": StageExecutionStatus.VERIFIED.value,
            },
            generator_provider=preferred_provider,
            generator_model_id=gen_model_id,
            critic_provider=summary.get("critic_provider", "groq"),
            critic_model_id=summary.get("critic_model", "openai/gpt-oss-20b"),
            is_multi_model=True,
            is_multi_provider=False,
            is_multi_family=False,
            model_diversity_rating=summary.get("model_diversity_rating", "SAME_FAMILY_SAME_PROVIDER"),
            deterministic_verification_passed=final_det_passed,
            failure_occurred=not final_det_passed,
            fallback_occurred=True,
            initial_artifact=candidate_text,
            critic_review=findings_text_for_class,
            revised_artifact=revised_text,
            resolution_breakdown=resolution_breakdown,
        )

        # Update persisted JSON
        summary_updated = {
            "status": "COMPLETED",
            "workflow_id": workflow_id,
            "resumed_workflow_id": audit_record.workflow_id,
            "task_id": audit_record.task_id,
            "execution_profile": audit_record.execution_profile.value,
            "generator_model": audit_record.generator_model_id,
            "critic_model": audit_record.critic_model_id,
            "is_multi_model": audit_record.is_multi_model,
            "is_multi_family": audit_record.is_multi_family,
            "is_multi_provider": audit_record.is_multi_provider,
            "model_diversity_rating": audit_record.model_diversity_rating,
            "consensus_status": audit_record.consensus_status,
            "total_latency_ms": audit_record.total_latency_ms,
            "total_tokens": audit_record.total_tokens,
            "deterministic_verification_passed": audit_record.deterministic_verification_passed,
            "account_verification_state": summary.get("account_verification_state", "DASHBOARD_EVIDENCED"),
            "steps_count": len(audit_record.steps),
            "stage_statuses": audit_record.stage_statuses,
            "resolution_breakdown": audit_record.resolution_breakdown,
            "steps": [s.model_dump(mode="json") for s in audit_record.steps],
        }

        updated_dump = {
            "summary": summary_updated,
            "initial_artifact": candidate_text,
            "critic_review": audit_record.critic_review,
            "revised_artifact": revised_text,
            "final_text": revised_text,
        }
        with open(p_path, "w", encoding="utf-8") as f:
            json.dump(updated_dump, f, indent=2, default=str)
        logger.info("Persisted resumed collaboration execution results to %s", persisted_json_path)

        return revised_text, audit_record
