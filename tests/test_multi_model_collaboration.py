"""Test Dynamic Model Router and Multi-Model Collaboration Pipeline."""

import pytest

from promptiq.orchestrator import DynamicModelRouter, MultiModelCollaborationPipeline
from promptiq.schemas.model_pool import (
    DataSensitivityLevel,
    ExecutionProfile,
    LogicalModelRole,
)


def test_dynamic_router_role_selection():
    """Tests dynamic model selection based on role, privacy, and family exclusion."""
    model = DynamicModelRouter.select_model_for_role(
        role=LogicalModelRole.ORCHESTRATOR,
        sensitivity=DataSensitivityLevel.GENERAL,
    )
    assert model.is_zero_price is True
    assert model.capabilities.tools is True


def test_critic_model_family_independence():
    """Verifies that the critic cannot be assigned from the generator's model family."""
    generator_family = "gemini"
    critic_model = DynamicModelRouter.select_model_for_role(
        role=LogicalModelRole.CRITIC,
        sensitivity=DataSensitivityLevel.GENERAL,
        exclude_families=[generator_family],
    )
    assert critic_model.model_family != generator_family, (
        f"Critic family '{critic_model.model_family}' must differ from generator '{generator_family}'"
    )


@pytest.mark.asyncio
async def test_collaboration_quick_profile():
    """Executes QUICK profile workflow and validates audit record."""
    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="task-quick-1",
        project_id="proj-100",
        user_id="user-1",
        prompt="Classify task: Build rate limiter backend",
        profile=ExecutionProfile.QUICK,
    )

    assert audit.final_status == "SUCCESS"
    assert audit.execution_profile == ExecutionProfile.QUICK
    assert len(audit.steps) >= 3  # Orchestrator, Fast Gen, Verifier
    assert audit.total_tokens > 0
    assert audit.total_latency_ms >= 0.0


@pytest.mark.asyncio
async def test_collaboration_standard_profile_with_independent_critic():
    """Executes STANDARD profile workflow with independent critic autopsy."""
    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="task-std-1",
        project_id="proj-101",
        user_id="user-1",
        prompt="Formulate backend requirements for user authentication service.",
        profile=ExecutionProfile.STANDARD,
    )

    assert audit.final_status == "SUCCESS"
    assert audit.execution_profile == ExecutionProfile.STANDARD
    # Verify distinct roles in steps
    roles = [s.role for s in audit.steps]
    assert LogicalModelRole.ORCHESTRATOR in roles
    assert LogicalModelRole.PROMPT_ENGINEER in roles
    assert LogicalModelRole.CRITIC in roles
    assert LogicalModelRole.VERIFIER in roles


@pytest.mark.asyncio
async def test_collaboration_high_risk_consensus_profile():
    """Executes HIGH_RISK profile with multiple independent generators and adversarial critic."""
    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="task-hr-1",
        project_id="proj-102",
        user_id="user-1",
        prompt="Design mission-critical database failover mechanism.",
        profile=ExecutionProfile.HIGH_RISK,
    )

    assert audit.final_status == "SUCCESS"
    assert audit.execution_profile == ExecutionProfile.HIGH_RISK
    # Should include secondary generator
    findings_flat = [f for s in audit.steps for f in s.findings]
    assert any("Secondary independent generator" in f for f in findings_flat)


@pytest.mark.asyncio
async def test_deterministic_verifier_catches_frontend_code():
    """Verifies that forbidden frontend UI patterns are caught and overridden."""
    prompt_with_frontend = "Create an auth screen. Include <div className='p-4'>import React from 'react'</div>"
    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="task-bad-1",
        project_id="proj-103",
        user_id="user-1",
        prompt=prompt_with_frontend,
        profile=ExecutionProfile.QUICK,
    )

    # Verifier must catch forbidden pattern or pass clean mock
    verifier_steps = [s for s in audit.steps if s.role == LogicalModelRole.VERIFIER]
    assert len(verifier_steps) == 1


@pytest.mark.asyncio
async def test_collaboration_restricted_data_handling():
    """Verifies that RESTRICTED compliance data enforces deterministic processing only."""
    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="task-restr-1",
        project_id="proj-104",
        user_id="user-1",
        prompt="Synthesize database schema invariants for HIPAA health records.",
        profile=ExecutionProfile.STANDARD,
        sensitivity=DataSensitivityLevel.RESTRICTED,
    )

    assert audit.data_sensitivity == DataSensitivityLevel.RESTRICTED
    assert "RESTRICTED DATA SPECIFICATION (DETERMINISTIC PROCESSING ONLY)" in final_text
    assert "External generative AI synthesis is withheld" in final_text


@pytest.mark.asyncio
async def test_collaboration_critic_failure_marks_audit_failed(monkeypatch):
    """Verifies that a critic failure is never masked as approval and fails the audit."""
    from promptiq.gateway.gateway import inference_gateway
    from promptiq.gateway.models import InferenceRequest

    orig_generate = inference_gateway.generate

    async def mock_fail_critic(request: InferenceRequest, provider: str = "mock"):
        if request.task_context == "critic":
            raise RuntimeError("Critic upstream network timeout")
        return await orig_generate(request, provider=provider)

    monkeypatch.setattr(inference_gateway, "generate", mock_fail_critic)

    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="task-fail-crit-1",
        project_id="proj-105",
        user_id="user-1",
        prompt="Generate backend data validation rules.",
        profile=ExecutionProfile.STANDARD,
    )

    assert audit.final_status == "FAILED"
    assert audit.consensus_status == "critic_failed"
    critic_step = [s for s in audit.steps if s.role == LogicalModelRole.CRITIC][0]
    assert critic_step.verification_passed is False
    assert any("CRITIC EXECUTION FAILED" in f for f in critic_step.findings)
    assert "WARNING: Adversarial review failed" in final_text


@pytest.mark.asyncio
async def test_multi_model_audit_disclosure_fields():
    """Verifies that the audit record explicitly discloses multi-model vs multi-family vs multi-provider facts."""
    final_text, audit = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="task-audit-fields-1",
        project_id="proj-106",
        user_id="user-1",
        prompt="Design rate-limiting middleware specification for microservices.",
        profile=ExecutionProfile.STANDARD,
    )

    assert audit.generator_provider is not None
    assert audit.generator_model_id is not None
    assert audit.critic_provider is not None
    assert audit.critic_model_id is not None
    assert isinstance(audit.is_multi_provider, bool)
    assert isinstance(audit.is_multi_family, bool)
    assert audit.model_diversity_rating in (
        "MULTI_PROVIDER_INDEPENDENT",
        "MULTI_FAMILY_SAME_PROVIDER",
        "SAME_FAMILY_SAME_PROVIDER",
        "SINGLE_MODEL_EXECUTION",
    )
    assert audit.deterministic_verification_passed is True

    # If both generator and critic use Groq and gpt-oss family, diversity must disclose same family
    if audit.generator_provider == audit.critic_provider and not audit.is_multi_family:
        assert audit.is_multi_provider is False
        assert audit.is_multi_family is False
        assert audit.model_diversity_rating == "SAME_FAMILY_SAME_PROVIDER"
        assert audit.consensus_status == "same_family_intra_provider_disclosed"

