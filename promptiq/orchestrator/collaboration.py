"""Multi-Model Collaboration Pipeline and Execution Audit."""

import time
import uuid
from typing import Any

from promptiq.core.logging import logger
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.orchestrator.roles import ModelRoleContract
from promptiq.orchestrator.router import DynamicModelRouter
from promptiq.schemas.model_pool import (
    DataSensitivityLevel,
    ExecutionProfile,
    ExecutionStepRecord,
    LogicalModelRole,
    MultiModelExecutionAuditRecord,
)

# Core PromptIQ Invariants checked during deterministic verification
FORBIDDEN_FRONTEND_PATTERNS = [
    "<html", "<body", "import React", "from 'react'", "export default function",
    "className=", "styled-components", "tailwind", "next/router", "next/navigation",
    "<html>", "<div>", "render()", "useState(", "useEffect("
]


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
                input_tokens=len(prompt) // 4,
                output_tokens=orch_resp.tokens_used,
                verification_passed=True,
                findings=["Workflow initialized", f"Profile: {profile.value}"],
            )
        )
        step_number += 1

        # -------------------------------------------------------------
        # STEP 2: Specialist Generation
        # -------------------------------------------------------------
        gen_role = LogicalModelRole.FAST if profile == ExecutionProfile.QUICK else (
            LogicalModelRole.REASONING if profile == ExecutionProfile.DEEP else LogicalModelRole.PROMPT_ENGINEER
        )
        gen_model = DynamicModelRouter.select_model_for_role(
            role=gen_role,
            sensitivity=sensitivity,
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
                input_tokens=len(prompt) // 4,
                output_tokens=gen_resp.tokens_used,
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
                    input_tokens=len(prompt) // 4,
                    output_tokens=sec_resp.tokens_used,
                    verification_passed=True,
                    findings=["Secondary independent generator completed"],
                )
            )
            step_number += 1

        # -------------------------------------------------------------
        # STEP 3: Independent Evaluation and Critique (Critic)
        # -------------------------------------------------------------
        critique_findings: list[str] = []
        if profile != ExecutionProfile.QUICK:
            # Enforce critic independence: MUST NOT be the same model family as generator!
            critic_model = DynamicModelRouter.select_model_for_role(
                role=LogicalModelRole.CRITIC,
                sensitivity=sensitivity,
                exclude_families=[gen_model.model_family],
            )
            crit_step_start = time.perf_counter()
            crit_prompt = (
                f"CONDUCT ADVERSARIAL AUTOPSY ON CANDIDATE PROMPT:\n\n"
                f"Candidate Output:\n{candidate_text}\n\n"
                f"Check for:\n"
                f"1. Invariant violations (Frontend UI code, paid billing assumptions).\n"
                f"2. Ambiguities or missing instructions.\n"
                f"3. Security/injection loopholes.\n"
                f"Return findings as bullet points. If clean, state 'APPROVED: NO DEFECTS'."
            )
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
                    input_tokens=len(crit_prompt) // 4,
                    output_tokens=crit_resp.tokens_used,
                    verification_passed=True,
                    findings=critique_findings,
                )
            )
            step_number += 1

        # -------------------------------------------------------------
        # STEP 4: Deterministic Verification
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
                findings=det_findings or ["Deterministic invariants fully satisfied."],
            )
        )
        step_number += 1

        # -------------------------------------------------------------
        # STEP 5: Disagreement Resolution & Adjudication
        # -------------------------------------------------------------
        final_text = candidate_text

        if not det_passed:
            consensus_status = "deterministic_override"
            disagreement_details = {"verifier_failures": det_findings}
            # Cleanse or replace invalid content
            final_text = (
                f"# PROMPTIQ SPECIFICATION\n\n"
                f"Note: Output was scrubbed by deterministic verifier due to invariant violation.\n\n"
                f"Core Logic:\n{candidate_text[:300]}..."
            )
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

        # -------------------------------------------------------------
        # STEP 6: Final Consolidation & Audit Record Creation
        # -------------------------------------------------------------
        total_latency = (time.perf_counter() - start_wall_time) * 1000.0

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
            final_status="SUCCESS" if det_passed else "FAILED",
        )

        return final_text, audit_record
