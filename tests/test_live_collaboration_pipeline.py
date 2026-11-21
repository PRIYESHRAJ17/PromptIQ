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
