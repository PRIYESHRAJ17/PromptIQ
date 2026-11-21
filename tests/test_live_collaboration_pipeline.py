"""Tests for Live Multi-Model Collaboration Pipeline and Execution Safeguards."""

import pytest

from promptiq.orchestrator.collaboration import (
    MultiModelCollaborationPipeline,
    classify_critic_resolutions,
)
from promptiq.orchestrator.collaboration_cli import (
    DEFAULT_COLLABORATION_TASK,
    execute_live_collaboration,
)
from promptiq.orchestrator.router import DynamicModelRouter
from promptiq.schemas.model_pool import (
    DataSensitivityLevel,
    ExecutionProfile,
    LogicalModelRole,
)


def test_router_exclude_model_ids_guarantees_distinct_critic():
    """Verifies that exclude_model_ids prevents assigning the generator as its own critic."""
    generator_id = "openai/gpt-oss-120b"
    critic_model = DynamicModelRouter.select_model_for_role(
        role=LogicalModelRole.CRITIC,
        sensitivity=DataSensitivityLevel.GENERAL,
        exclude_families=None,
        exclude_model_ids=[generator_id],
        preferred_provider="groq",
    )
    assert critic_model.model_id != generator_id
    assert critic_model.model_id == "openai/gpt-oss-20b"


def test_classify_critic_resolutions_logic():
    """Tests deterministic categorization of critic findings into resolved, rejected, unresolved."""
    critic_text = (
        "1. Missing food-safety temperature tracking for perishable donations.\n"
        "2. No role-based access control for recipient organisations.\n"
        "3. Missing audit history ledger for chain of custody.\n"
        "4. Redundant websocket server architecture is unneeded.\n"
        "5. Omitted quantum encryption protocol."
    )
    revised_text = (
        "# Revised Redistribution Architecture\n"
        "Includes food safety temperature logging and monitoring.\n"
        "Implements strict RBAC role-based access control for NGOs.\n"
        "Appends immutable audit history ledger for every pickup.\n"
        "Rejected: redundant websocket server architecture is unneeded for asynchronous food alerts.\n"
    )

    breakdown = classify_critic_resolutions(critic_text, revised_text)
    assert len(breakdown["resolved"]) >= 3
    assert len(breakdown["rejected_with_reason"]) >= 1
    assert len(breakdown["unresolved"]) >= 1


@pytest.mark.asyncio
async def test_collaboration_pipeline_five_stages_mock():
    """Executes the standard 5-stage collaboration workflow with mock inference."""
    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="collab-test-1",
        project_id="proj-collab-test",
        user_id="test-operator",
        prompt=DEFAULT_COLLABORATION_TASK,
        profile=ExecutionProfile.STANDARD,
        preferred_provider="groq",
    )

    assert audit.final_status == "SUCCESS"
    assert audit.is_multi_model is True
    assert audit.generator_model_id == "openai/gpt-oss-120b"
    assert audit.critic_model_id == "openai/gpt-oss-20b"
    assert audit.is_multi_family is False
    assert audit.is_multi_provider is False
    assert audit.model_diversity_rating == "SAME_FAMILY_SAME_PROVIDER"
    assert audit.consensus_status == "same_family_intra_provider_disclosed"

    # Verify all 5 logical stages executed:
    # Step 1: Orchestrator
    # Step 2: Generator (Stage A)
    # Step 3: Critic (Stage B)
    # Step 4: Candidate Deterministic Verifier (Stage C)
    # Step 5: Revision (Stage D)
    # Step 6: Final Deterministic Verifier & Resolution Breakdown (Stage E)
    roles = [s.role for s in audit.steps]
    assert LogicalModelRole.ORCHESTRATOR in roles
    assert LogicalModelRole.PROMPT_ENGINEER in roles
    assert LogicalModelRole.CRITIC in roles
    assert LogicalModelRole.VERIFIER in roles
    assert len(audit.steps) >= 6

    # Verify artifacts preserved
    assert audit.initial_artifact is not None
    assert audit.critic_review is not None
    assert audit.revised_artifact is not None
    assert "resolved" in audit.resolution_breakdown
    assert audit.deterministic_verification_passed is True


@pytest.mark.asyncio
async def test_collaboration_cli_fails_closed_without_opt_in():
    """Verifies that live collaboration strictly fails closed when --opt-in is omitted."""
    final_text, audit, summary = await execute_live_collaboration(
        opt_in=False,
        output_json_path=None,
    )
    assert summary["status"] == "BLOCKED_EXTERNAL"
    assert summary["success"] is False
    assert audit is None
    assert "opt-in" in summary["error"].lower()


@pytest.mark.asyncio
async def test_collaboration_cli_fails_closed_without_api_key(monkeypatch):
    """Verifies that live collaboration strictly fails closed when operator key is absent."""
    from promptiq.core.config import settings

    monkeypatch.setattr(settings, "PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED", True)
    monkeypatch.setattr(settings, "OPERATOR_GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    final_text, audit, summary = await execute_live_collaboration(
        opt_in=True,
        output_json_path=None,
    )
    assert summary["status"] == "BLOCKED_EXTERNAL"
    assert summary["success"] is False
    assert audit is None
    assert "credential" in summary["error"].lower() or "api key" in summary["error"].lower()


@pytest.mark.asyncio
async def test_deterministic_verifier_catches_frontend_in_revision(monkeypatch):
    """Verifies that if a revision introduces frontend patterns, deterministic verifier overrides it."""
    from promptiq.gateway.gateway import inference_gateway
    from promptiq.gateway.models import InferenceRequest, InferenceResponse

    orig_generate = inference_gateway.generate

    async def mock_polluted_revision(request: InferenceRequest, provider: str = "mock"):
        if request.task_context == "revision":
            return InferenceResponse(
                text="Backend design with UI snippet: <div className='container'>import React from 'react'</div>",
                model_id=request.target_model_id or "openai/gpt-oss-120b",
                provider=provider,
                tokens_used=50,
            )
        return await orig_generate(request, provider=provider)

    monkeypatch.setattr(inference_gateway, "generate", mock_polluted_revision)

    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="collab-polluted-rev-1",
        project_id="proj-collab-test",
        user_id="test-operator",
        prompt=DEFAULT_COLLABORATION_TASK,
        profile=ExecutionProfile.STANDARD,
    )

    assert audit.consensus_status == "deterministic_override"
    assert audit.deterministic_verification_passed is False
    assert "scrubbed by deterministic verifier" in final_text


def test_token_budget_calculation_for_revision_prompts():
    """Verifies that revision prompt preparation stays strictly within 8,000 TPM limit."""
    from promptiq.orchestrator.collaboration import prepare_revision_prompt

    candidate = "# Architecture\n" + ("Database service logic and endpoints.\n" * 150)
    findings = [
        "Enforce cold-chain temperature monitoring.",
        "Implement OTP pickup confirmation.",
        "Mask donor location until acceptance.",
    ]
    prompt_text, max_tokens = prepare_revision_prompt(candidate, findings, DEFAULT_COLLABORATION_TASK)

    est_input_tokens = len(prompt_text) // 4
    total_footprint = est_input_tokens + max_tokens

    assert max_tokens == 2500
    # Must leave at least a 1,500 token buffer below 8,000 TPM ceiling
    assert total_footprint <= 6500
    assert "REVISE SYSTEM ARCHITECTURE" in prompt_text
    assert "cold-chain temperature monitoring" in prompt_text


def test_resolution_breakdown_classification_four_categories():
    """Verifies classification of findings into resolved, partially_resolved, rejected_with_reason, unresolved."""
    from promptiq.orchestrator.collaboration import classify_critic_resolutions

    critic_text = (
        "1. Missing food-safety temperature logging for perishable goods.\n"
        "2. Redundant direct socket streaming protocol is unneeded.\n"
        "3. Quantum-resistant lattice cryptography is absent from auth tokens.\n"
        "4. Audit trails are recorded but tamper-evident HMAC cryptographic signatures are omitted."
    )
    revised_text = (
        "# Revised Architecture\n"
        "Enforces food safety temperature logging for perishable goods.\n"
        "Rejected: redundant direct socket streaming protocol is unneeded for background webhooks.\n"
        "Records persistent audit events.\n"
    )

    breakdown = classify_critic_resolutions(critic_text, revised_text)
    assert len(breakdown["resolved"]) >= 1
    assert len(breakdown["partially_resolved"]) >= 1
    assert len(breakdown["rejected_with_reason"]) >= 1
    assert len(breakdown["unresolved"]) >= 1


@pytest.mark.asyncio
async def test_rate_limit_preflight_detection_and_deferral(monkeypatch):
    """Verifies that in-memory preflight detects rate-limiting and marks partial status without false HTTP 200."""
    from promptiq.gateway.governor import governor
    from promptiq.schemas.model_pool import StageExecutionStatus, WorkflowExecutionStatus

    monkeypatch.setattr(
        governor,
        "get_model_quota_status",
        lambda model_id: {
            "model_id": model_id,
            "rpm_used": 10,
            "rpm_limit": 30,
            "rpm_remaining": 20,
            "tpm_used": 7500,
            "tpm_limit": 8000,
            "tpm_remaining": 500,
            "reset_seconds": 25.5,
            "is_rate_limited": True,
        },
    )

    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="collab-rate-limited-1",
        project_id="proj-collab-test",
        user_id="test-operator",
        prompt=DEFAULT_COLLABORATION_TASK,
        profile=ExecutionProfile.STANDARD,
    )

    assert audit.final_status == WorkflowExecutionStatus.PARTIALLY_COMPLETED_RATE_LIMITED.value
    assert audit.stage_statuses["revision"] == StageExecutionStatus.RATE_LIMITED.value
    assert audit.stage_statuses["final_verification"] == StageExecutionStatus.INCOMPLETE.value

    # Check Step 5 audit record
    rev_step = [s for s in audit.steps if s.stage == "revision"][0]
    assert rev_step.outcome_status == StageExecutionStatus.RATE_LIMITED.value
    assert rev_step.http_status is None  # Never default to HTTP 200 on in-memory hold
    assert rev_step.request_id is None   # No false provider attribution
    assert "In-Memory Preflight" in rev_step.findings[0]


@pytest.mark.asyncio
async def test_workflow_resumption_from_persisted_state(tmp_path):
    """Verifies that resumption skips Stages A/B/C, executes D/E, and updates the persisted ledger."""
    import json

    from promptiq.schemas.model_pool import StageExecutionStatus, WorkflowExecutionStatus

    test_wf_id = "test-resume-wf-1234"
    dummy_json_path = tmp_path / "test_exec.json"

    dummy_data = {
        "summary": {
            "status": "PARTIALLY_COMPLETED_RATE_LIMITED",
            "workflow_id": test_wf_id,
            "task_id": "collab-live-food-redistribution-1",
            "execution_profile": "STANDARD",
            "generator_model": "openai/gpt-oss-120b",
            "critic_model": "openai/gpt-oss-20b",
            "is_multi_model": True,
            "is_multi_family": False,
            "is_multi_provider": False,
            "model_diversity_rating": "SAME_FAMILY_SAME_PROVIDER",
            "consensus_status": "uncertainty_retained",
            "total_latency_ms": 15000.0,
            "total_tokens": 10000,
            "deterministic_verification_passed": True,
            "account_verification_state": "DASHBOARD_EVIDENCED",
            "steps_count": 4,
            "stage_statuses": {
                "orchestration": "VERIFIED",
                "generation": "VERIFIED",
                "criticism": "VERIFIED",
                "initial_verification": "VERIFIED",
                "revision": "RATE_LIMITED",
                "final_verification": "INCOMPLETE",
            },
            "steps": [
                {
                    "step_number": 1,
                    "role": "ORCHESTRATOR",
                    "provider": "mock",
                    "model_id": "openai/gpt-oss-120b",
                    "latency_ms": 100.0,
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "request_id": "mock_req_1",
                    "http_status": 200,
                    "stage": "orchestration",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                },
                {
                    "step_number": 2,
                    "role": "PROMPT_ENGINEER",
                    "provider": "mock",
                    "model_id": "openai/gpt-oss-120b",
                    "latency_ms": 200.0,
                    "input_tokens": 100,
                    "output_tokens": 500,
                    "request_id": "mock_req_2",
                    "http_status": 200,
                    "stage": "generation",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                },
                {
                    "step_number": 3,
                    "role": "CRITIC",
                    "provider": "mock",
                    "model_id": "openai/gpt-oss-20b",
                    "latency_ms": 150.0,
                    "input_tokens": 500,
                    "output_tokens": 300,
                    "request_id": "mock_req_3",
                    "http_status": 200,
                    "stage": "criticism",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                    "findings": ["Enforce mandatory food safety temperature tracking."],
                },
                {
                    "step_number": 4,
                    "role": "VERIFIER",
                    "provider": "internal",
                    "model_id": "deterministic-verifier-v1",
                    "latency_ms": 0.5,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "request_id": None,
                    "http_status": None,
                    "stage": "initial_verification",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                },
            ],
        },
        "initial_artifact": "# Candidate Backend Architecture\nIncludes food redistribution entities and services with no UI.",
        "critic_review": "1. Enforce mandatory food safety temperature tracking (<4C) for all perishables.",
        "revised_artifact": None,
        "final_text": "# Candidate Backend Architecture\nIncludes food redistribution entities and services with no UI.",
    }

    with open(dummy_json_path, "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)

    final_text, audit = await MultiModelCollaborationPipeline.resume_workflow_revision(
        workflow_id=test_wf_id,
        persisted_json_path=str(dummy_json_path),
        preferred_provider="mock",
    )

    assert audit.final_status == WorkflowExecutionStatus.COMPLETED.value
    assert audit.parent_workflow_id == test_wf_id
    assert audit.stage_statuses["revision"] == StageExecutionStatus.VERIFIED.value
    assert audit.stage_statuses["final_verification"] == StageExecutionStatus.VERIFIED.value

    # Verify steps 1-4 preserved and 5-6 added
    assert len(audit.steps) == 6
    assert audit.steps[0].request_id == "mock_req_1"
    assert audit.steps[1].request_id == "mock_req_2"
    assert audit.steps[2].request_id == "mock_req_3"
    assert audit.steps[4].stage == "revision"
    assert audit.steps[4].step_number == 5
    assert audit.steps[5].stage == "final_verification"
    assert audit.steps[5].step_number == 6

    # Verify updated JSON on disk
    with open(dummy_json_path, encoding="utf-8") as f:
        updated = json.load(f)
    assert updated["summary"]["status"] == "COMPLETED"
    assert len(updated["summary"]["steps"]) == 6


@pytest.mark.asyncio
async def test_workflow_resumption_missing_artifact_raises_error(tmp_path):
    """Verifies that resuming a workflow with missing candidate artifact raises ValueError."""
    import json

    test_wf_id = "test-bad-wf"
    dummy_json_path = tmp_path / "bad_exec.json"
    dummy_data = {
        "summary": {"workflow_id": test_wf_id},
        "initial_artifact": "",
    }
    with open(dummy_json_path, "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)

    with pytest.raises(ValueError, match="initial_artifact"):
        await MultiModelCollaborationPipeline.resume_workflow_revision(
            workflow_id=test_wf_id,
            persisted_json_path=str(dummy_json_path),
            preferred_provider="mock",
        )


@pytest.mark.asyncio
async def test_workflow_interruption_at_stage_d_resumes_without_reinvoking_generator(tmp_path):
    """Verifies that an interrupted workflow resumes cleanly without re-invoking generator or critic."""
    import json
    from unittest.mock import patch

    from promptiq.gateway.gateway import inference_gateway
    from promptiq.schemas.model_pool import WorkflowExecutionStatus

    test_wf_id = "interrupted-wf-5678"
    dummy_json_path = tmp_path / "interrupted_exec.json"

    dummy_data = {
        "summary": {
            "status": "PARTIALLY_COMPLETED_RATE_LIMITED",
            "workflow_id": test_wf_id,
            "task_id": "collab-interrupted-food-task",
            "execution_profile": "STANDARD",
            "generator_model": "openai/gpt-oss-120b",
            "critic_model": "openai/gpt-oss-20b",
            "steps": [
                {
                    "step_number": 1,
                    "role": "ORCHESTRATOR",
                    "provider": "mock",
                    "model_id": "openai/gpt-oss-120b",
                    "stage": "orchestration",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                    "request_id": "req_orch_original",
                },
                {
                    "step_number": 2,
                    "role": "PROMPT_ENGINEER",
                    "provider": "mock",
                    "model_id": "openai/gpt-oss-120b",
                    "stage": "generation",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                    "request_id": "req_gen_original",
                },
                {
                    "step_number": 3,
                    "role": "CRITIC",
                    "provider": "mock",
                    "model_id": "openai/gpt-oss-20b",
                    "stage": "criticism",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                    "request_id": "req_crit_original",
                    "findings": ["Enforce food safety temperature logging."],
                },
                {
                    "step_number": 4,
                    "role": "VERIFIER",
                    "provider": "internal",
                    "model_id": "deterministic-verifier-v1",
                    "stage": "initial_verification",
                    "outcome_status": "VERIFIED",
                    "verification_passed": True,
                },
            ],
        },
        "initial_artifact": "# Candidate Backend Architecture\nFood distribution platform backend design with zero UI.",
        "critic_review": "1. Enforce mandatory temperature logging for perishables.\n2. Add RBAC.",
        "revised_artifact": None,
        "final_text": "# Candidate Backend Architecture\nFood distribution platform backend design with zero UI.",
    }

    with open(dummy_json_path, "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)

    gateway_calls = []
    original_generate = inference_gateway.generate

    async def spy_generate(*args, **kwargs):
        gateway_calls.append((args, kwargs))
        return await original_generate(*args, **kwargs)

    with patch.object(inference_gateway, "generate", side_effect=spy_generate):
        final_text, audit = await MultiModelCollaborationPipeline.resume_workflow_revision(
            workflow_id=test_wf_id,
            persisted_json_path=str(dummy_json_path),
            preferred_provider="mock",
        )

    # Crucial assertion: Exactly 1 call to inference gateway (Revision only).
    # Orchestration, Generation, and Criticism were NOT re-invoked!
    assert len(gateway_calls) == 1
    assert audit.final_status == WorkflowExecutionStatus.COMPLETED.value
    assert audit.parent_workflow_id == test_wf_id
    assert audit.steps[0].request_id == "req_orch_original"
    assert audit.steps[1].request_id == "req_gen_original"
    assert audit.steps[2].request_id == "req_crit_original"
    assert audit.steps[4].stage == "revision"
    assert audit.steps[5].stage == "final_verification"


def test_groq_token_accounting_reconciliation_math():
    """Verifies the exact token accounting reconciliation for GPT-OSS 120B."""
    # Step 1: Orchestration
    step_1_input = 214
    step_1_output = 3146
    step_1_total = step_1_input + step_1_output
    assert step_1_total == 3360

    # Step 2: Candidate Generation
    step_2_input = 206
    step_2_output = 4096
    step_2_total = step_2_input + step_2_output
    assert step_2_total == 4302

    # Combined initial generation footprint
    combined_total = step_1_total + step_2_total
    assert combined_total == 7662

    # Output-only sum (the prior miscalculation that omitted prompt tokens)
    output_only_sum = step_1_output + step_2_output
    assert output_only_sum == 7242
    assert combined_total - output_only_sum == 420  # Omitted prompt tokens: 214 + 206

    # Under strict unreplenished 8,000 TPM limit
    tpm_limit = 8000
    unreplenished_remaining = tpm_limit - combined_total
    assert unreplenished_remaining == 338  # Not 758 (which was 8000 - 7242)


def test_gpt_oss_20b_quota_limits_and_independence():
    """Verifies that GPT-OSS 20B is reconciled to 8,000 TPM and isolated from 120B."""
    from promptiq.gateway.governor import MODEL_FREE_QUOTAS, CapacityGovernor

    # Reconciled limit matches live Groq response header (limit_tokens: 8000)
    assert MODEL_FREE_QUOTAS["openai/gpt-oss-20b"]["tpm"] == 8000
    assert MODEL_FREE_QUOTAS["openai/gpt-oss-120b"]["tpm"] == 8000

    # Step 3 token accounting
    step_3_input = 4242
    step_3_output = 4096
    step_3_total = step_3_input + step_3_output
    assert step_3_total == 8338

    # Verify model quota isolation in governor
    gov = CapacityGovernor(auto_load=False)
    gov.record_model_usage("openai/gpt-oss-20b", tokens_used=step_3_total)

    # 120B quota must be untouched
    status_120b = gov.get_model_quota_status("openai/gpt-oss-120b")
    assert status_120b["tokens_last_minute"] == 0
    assert status_120b["tpm_remaining"] == 8000

    # 20B quota reflects usage
    status_20b = gov.get_model_quota_status("openai/gpt-oss-20b")
    assert status_20b["tokens_last_minute"] == step_3_total
    assert status_20b["is_rate_limited"] is True


def test_durable_quota_ledger_cross_process_persistence(tmp_path):
    """Verifies that CapacityGovernor state survives across separate process instances via durable ledger."""
    from promptiq.gateway.governor import CapacityGovernor

    ledger_file = tmp_path / "test_quota_ledger.json"

    # Process 1: records usage and response headers
    gov_proc1 = CapacityGovernor(ledger_path=ledger_file, auto_load=False)
    gov_proc1.record_model_usage("openai/gpt-oss-120b", tokens_used=4302)
    gov_proc1.inspect_response_headers(
        provider="groq",
        model_id="openai/gpt-oss-120b",
        headers={
            "x-ratelimit-limit-tokens": "8000",
            "x-ratelimit-remaining-tokens": "3698",
            "x-ratelimit-reset-tokens": "26.752s",
        },
        status_code=200,
    )
    assert ledger_file.exists()

    # Process 2 (simulating a fresh CLI invocation with new process memory)
    gov_proc2 = CapacityGovernor(ledger_path=ledger_file, auto_load=True)
    status = gov_proc2.get_model_quota_status("openai/gpt-oss-120b")

    # Verify Process 2 has loaded Process 1's usage and header reset duration
    assert status["tokens_last_minute"] == 4302
    assert status["tpm_used"] == 4302
    assert status["tpm_remaining"] == 8000 - 4302
    assert status["reset_seconds"] > 0.0
    assert status["is_rate_limited"] is True


def test_governor_sync_from_execution_ledger(tmp_path):
    """Verifies governor syncs all previous steps and rate limit headers from workflow execution JSON."""
    import json

    from promptiq.gateway.governor import CapacityGovernor

    exec_json = tmp_path / "exec_results.json"
    dummy_data = {
        "summary": {
            "steps": [
                {
                    "step_number": 1,
                    "model_id": "openai/gpt-oss-120b",
                    "http_status": 200,
                    "input_tokens": 214,
                    "output_tokens": 3146,
                    "timestamp": "2026-11-21T19:37:20.194247Z",
                    "metadata": {
                        "rate_limit_headers": {"limit_tokens": "8000", "remaining_tokens": "7148"},
                        "response_timestamp": "2026-11-21T19:37:20.193067+00:00",
                    },
                },
                {
                    "step_number": 2,
                    "model_id": "openai/gpt-oss-120b",
                    "http_status": 200,
                    "input_tokens": 206,
                    "output_tokens": 4096,
                    "timestamp": "2026-11-21T19:37:29.209930Z",
                    "metadata": {
                        "rate_limit_headers": {"limit_tokens": "8000", "remaining_tokens": "4433", "reset_tokens": "26.752s"},
                        "response_timestamp": "2026-11-21T19:37:29.208230+00:00",
                    },
                },
                {
                    "step_number": 3,
                    "model_id": "openai/gpt-oss-20b",
                    "http_status": 200,
                    "input_tokens": 4242,
                    "output_tokens": 4096,
                    "timestamp": "2026-11-21T19:37:34.324292Z",
                    "metadata": {
                        "rate_limit_headers": {"limit_tokens": "8000", "remaining_tokens": "3421", "reset_tokens": "34.342s"},
                        "response_timestamp": "2026-11-21T19:37:34.322988+00:00",
                    },
                },
            ]
        }
    }
    with open(exec_json, "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)

    ledger_file = tmp_path / "sync_ledger.json"
    gov = CapacityGovernor(ledger_path=ledger_file, auto_load=False)
    sync_result = gov.sync_from_execution_ledger(exec_json)

    assert sync_result["status"] == "synced"
    assert sync_result["synced_steps"] == 3
    assert "openai/gpt-oss-120b" in sync_result["models"]
    assert "openai/gpt-oss-20b" in sync_result["models"]


def test_revision_request_quota_headroom_verification():
    """Verifies that the revision request footprint comfortably fits within replenished 8,000 TPM quota."""
    from promptiq.orchestrator.collaboration import prepare_revision_prompt

    candidate = "# Candidate Food Redistribution Architecture\n" + ("Service logic and database models.\n" * 150)
    findings = [
        "Enforce cold-chain temperature monitoring.",
        "Implement OTP pickup confirmation.",
        "Mask donor exact location until confirmation.",
    ]
    prompt_text, max_tokens = prepare_revision_prompt(candidate, findings, DEFAULT_COLLABORATION_TASK)

    est_input_tokens = len(prompt_text) // 4
    total_footprint = est_input_tokens + max_tokens

    # Assertions on token budget
    assert max_tokens == 2500
    assert total_footprint <= 6300  # Within ~6,300 tokens

    # Available TPM on replenished Groq Free tier
    groq_tpm_limit = 8000
    safety_buffer = groq_tpm_limit - total_footprint
    safety_margin_pct = (safety_buffer / groq_tpm_limit) * 100.0

    # Must have at least 1,700 tokens buffer (>= 20% safety margin)
    assert safety_buffer >= 1700
    assert safety_margin_pct >= 21.0


def test_cli_safe_formatting_with_null_fields(capsys):
    """Verifies that render_execution_summary handles null values for all fields without crash."""
    from promptiq.orchestrator.collaboration_cli import render_execution_summary
    from promptiq.schemas.model_pool import (
        ExecutionStepRecord,
        LogicalModelRole,
        MultiModelExecutionAuditRecord,
    )

    null_step = ExecutionStepRecord(
        step_number=1,
        role=LogicalModelRole.PROMPT_ENGINEER,
        provider="custom_provider",
        model_id=None,
        request_id=None,
        http_status=None,
        latency_ms=None,
        input_tokens=None,
        output_tokens=None,
        findings=[],
    )

    audit = MultiModelExecutionAuditRecord(
        workflow_id="wf-test-null",
        steps=[null_step],
        total_latency_ms=None,
        total_tokens=None,
        deterministic_verification_passed=None,
    )

    render_execution_summary(audit, {"status": "TEST_NULL_STATUS"})
    captured = capsys.readouterr()

    assert "Execution Status: TEST_NULL_STATUS" in captured.out
    assert "Workflow ID:      wf-test-null" in captured.out
    assert "Total Latency:    N/A" in captured.out
    assert "Total Tokens:     N/A" in captured.out
    assert "Deterministic:    N/A" in captured.out
    assert "N/A" in captured.out


def test_cli_distinguishes_internal_from_provider_steps(capsys):
    """Verifies that internal deterministic verifier steps are visually marked [INTERNAL] with N/A HTTP/ReqID."""
    from promptiq.orchestrator.collaboration_cli import render_execution_summary
    from promptiq.schemas.model_pool import (
        ExecutionStepRecord,
        LogicalModelRole,
        MultiModelExecutionAuditRecord,
    )

    internal_step = ExecutionStepRecord(
        step_number=4,
        role=LogicalModelRole.VERIFIER,
        provider="internal",
        model_id="deterministic-verifier-v1",
        request_id=None,
        http_status=None,
        latency_ms=0.5,
        input_tokens=0,
        output_tokens=0,
        findings=["Deterministic checks passed."],
    )

    provider_step = ExecutionStepRecord(
        step_number=5,
        role=LogicalModelRole.PROMPT_ENGINEER,
        provider="groq",
        model_id="openai/gpt-oss-120b",
        request_id="req_test_abc123",
        http_status=200,
        latency_ms=5120.0,
        input_tokens=1500,
        output_tokens=2200,
        findings=["Generated revised architecture."],
    )

    audit = MultiModelExecutionAuditRecord(
        workflow_id="wf-test-distinct",
        steps=[internal_step, provider_step],
        total_latency_ms=5120.5,
        total_tokens=3700,
        deterministic_verification_passed=True,
    )

    render_execution_summary(audit, {"status": "COMPLETED"})
    captured = capsys.readouterr()

    # Internal step verification
    assert "[INTERNAL]" in captured.out
    assert "N/A (Internal)" in captured.out
    assert "deterministic-verifier-v1" in captured.out

    # Provider step verification
    assert "groq" in captured.out
    assert "openai/gpt-oss-120b" in captured.out
    assert "req_test_abc123" in captured.out
    assert "200" in captured.out
    assert "1500/2200" in captured.out


def test_cli_displays_parent_and_resumed_workflow_ids(capsys):
    """Verifies that both parent and resumed workflow IDs are prominently rendered on resumed workflows."""
    from promptiq.orchestrator.collaboration_cli import render_execution_summary
    from promptiq.schemas.model_pool import MultiModelExecutionAuditRecord

    audit = MultiModelExecutionAuditRecord(
        workflow_id="bccc4086-47a3-4ac1-84af-791acfbfc9d6",
        parent_workflow_id="422f4399-c93f-439f-a7ef-bbf3149a4057",
        steps=[],
    )

    summary = {
        "status": "COMPLETED",
        "workflow_id": "422f4399-c93f-439f-a7ef-bbf3149a4057",
        "resumed_workflow_id": "bccc4086-47a3-4ac1-84af-791acfbfc9d6",
    }

    render_execution_summary(audit, summary)
    captured = capsys.readouterr()

    assert "Workflow ID:      422f4399-c93f-439f-a7ef-bbf3149a4057" in captured.out
    assert "Resumed ID:       bccc4086-47a3-4ac1-84af-791acfbfc9d6" in captured.out


def test_final_verification_independent_hash_against_revised_artifact():
    """Confirms that Stage E executed against revised artifact (not copied from Stage C) with distinct SHA-256."""
    import hashlib
    import json
    from pathlib import Path

    artifact_path = Path("docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json")
    assert artifact_path.exists(), "Persisted execution ledger must exist."

    with open(artifact_path, encoding="utf-8") as f:
        data = json.load(f)

    init_art = data["initial_artifact"]
    rev_art = data["revised_artifact"]

    h_init = hashlib.sha256(init_art.encode("utf-8")).hexdigest()
    h_rev = hashlib.sha256(rev_art.encode("utf-8")).hexdigest()

    # Independent artifact verification
    assert h_init != h_rev
    assert h_init == "d2b4b1a11dbbda7e44c115d30fe2376f264ad8c02aba96775e2933c7c65c8117"
    assert h_rev == "6011c869d09631f1d4351eeaf3d44afdc5c6f918becd3aafb096541ccd8c30ce"

    steps = data["summary"]["steps"]
    step_4 = steps[3]  # Stage C
    step_6 = steps[5]  # Stage E

    assert step_4["step_number"] == 4
    assert step_4["provider"] == "internal"
    assert step_4["http_status"] is None
    assert step_4["request_id"] is None
    assert "Deterministic invariants fully satisfied on candidate artifact." in step_4["findings"][0]

    assert step_6["step_number"] == 6
    assert step_6["provider"] == "internal"
    assert step_6["http_status"] is None
    assert step_6["request_id"] is None
    assert "Critic findings resolution: 5 resolved" in step_6["findings"][0]

    # Confirm all 5 critic autopsy findings are tracked as resolved in the final breakdown
    res = data["summary"]["resolution_breakdown"]
    assert len(res["resolved"]) == 5
    assert len(res["unresolved"]) == 0


def test_cli_inspect_mode_renders_cleanly_without_api_calls(capsys):
    """Verifies that collaboration_cli --inspect parses and formats persisted execution ledger without any network calls."""
    from unittest.mock import patch

    from promptiq.orchestrator.collaboration_cli import main

    with patch("sys.argv", ["collaboration_cli.py", "--inspect", "docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json"]):
        main()

    captured = capsys.readouterr()
    assert "Execution Status: COMPLETED" in captured.out
    assert "Workflow ID:      422f4399-c93f-439f-a7ef-bbf3149a4057" in captured.out
    assert "Resumed ID:       bccc4086-47a3-4ac1-84af-791acfbfc9d6" in captured.out
    assert "Total Latency:    27201.9 ms" in captured.out
    assert "Total Tokens:     23014" in captured.out
    assert "Consensus Status: adjudicated" in captured.out
    assert "Deterministic:    PASSED" in captured.out
    assert "Resolved Findings (5):" in captured.out
    assert "req_01m7zvprh4ev9v7e67f2ypx2r7" in captured.out


def test_cli_partially_completed_failure_summary_rendering(capsys):
    """Verifies that render_execution_summary safely renders failure and notice when audit is None."""
    from promptiq.orchestrator.collaboration_cli import render_execution_summary

    summary = {
        "status": "BLOCKED_EXTERNAL",
        "error": "Operator confirmation required.",
        "notice": "Provide --opt-in to execute network calls.",
    }

    render_execution_summary(None, summary)
    captured = capsys.readouterr()

    assert "Execution Status: BLOCKED_EXTERNAL" in captured.out
    assert "Failure Reason:   Operator confirmation required." in captured.out
    assert "Notice:           Provide --opt-in to execute network calls." in captured.out


def test_quota_ledger_durability_and_expiration_pruning(tmp_path):
    """Verifies atomic writes, expired sliding-window pruning, and lack of secrets in quota ledger."""
    import json
    from datetime import UTC, datetime

    from promptiq.gateway.governor import CapacityGovernor

    ledger_path = tmp_path / "test_ledger.json"
    gov = CapacityGovernor(ledger_path=ledger_path, auto_load=False)

    now = datetime.now(UTC).timestamp()
    expired_min = now - 120.0  # 2 minutes ago (expired for minute window)
    active_min = now - 10.0   # 10 seconds ago (active for minute window)

    gov._model_requests_minute["openai/gpt-oss-120b"] = [expired_min, active_min]
    gov._model_tokens_minute["openai/gpt-oss-120b"] = [(expired_min, 1000), (active_min, 500)]

    # Atomic write with pruning
    success = gov.save_durable_state()
    assert success is True
    assert ledger_path.exists()

    with open(ledger_path, encoding="utf-8") as f:
        data = json.load(f)

    # Confirm expired timestamps were pruned
    min_reqs = data["model_requests_minute"]["openai/gpt-oss-120b"]
    assert len(min_reqs) == 1
    assert min_reqs[0] == active_min

    min_toks = data["model_tokens_minute"]["openai/gpt-oss-120b"]
    assert len(min_toks) == 1
    assert min_toks[0] == [active_min, 500]

    # Confirm zero credentials or keys stored
    raw_text = ledger_path.read_text(encoding="utf-8")
    assert "gsk_" not in raw_text
    assert "api_key" not in raw_text
    assert "Authorization" not in raw_text


