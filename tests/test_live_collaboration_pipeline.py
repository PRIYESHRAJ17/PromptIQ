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
