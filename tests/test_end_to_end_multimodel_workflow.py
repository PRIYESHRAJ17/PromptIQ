"""Comprehensive 16-Step End-to-End Multi-Model Workflow Integration Test."""

import pytest
from httpx import AsyncClient

from promptiq.compiler.pps import PPSBuilder
from promptiq.models.constitution import ProjectConstitution
from promptiq.orchestrator import MultiModelCollaborationPipeline
from promptiq.schemas.model_pool import ExecutionProfile, LogicalModelRole
from promptiq.schemas.pps import TargetProfileSchema


@pytest.mark.asyncio
async def test_complete_sixteen_step_promptiq_lifecycle(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Executes and rigorously asserts the complete 16-step PromptIQ product lifecycle."""
    # -------------------------------------------------------------
    # STEP 1: IDEA INTAKE
    # -------------------------------------------------------------
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "End-to-End Incident Command", "description": "16-step lifecycle verification"},
        headers=user_auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    intake_payload = {
        "goal": "Build high-throughput incident dispatch daemon in Python",
        "deliverable": "complete_package",
        "target": "google-antigravity",
        "target_mode": "specific",
        "context_text": "Must process alerts from PagerDuty and dispatch to Slack. Zero-price internal execution.",
        "depth": "guided",
        "task_type": "software_project",
    }
    start_resp = await client.post(
        f"/api/v1/projects/{project_id}/discovery/start",
        json=intake_payload,
        headers=user_auth_headers,
    )
    assert start_resp.status_code == 201
    discovery_data = start_resp.json()
    session_id = discovery_data["id"]

    # -------------------------------------------------------------
    # STEP 2: ADAPTIVE DISCOVERY (QUESTIONS)
    # -------------------------------------------------------------
    next_questions = discovery_data.get("next_questions", [])
    assert len(next_questions) > 0

    # -------------------------------------------------------------
    # STEP 3: ANSWERS SUBMISSION
    # -------------------------------------------------------------
    ans_payload = {
        "answers": {
            "problem_statement": "Incident alerts are currently lost without centralized queueing.",
            "target_scale": "5,000 webhook events per minute with burst handling.",
        }
    }
    ans_resp = await client.post(
        f"/api/v1/projects/{project_id}/discovery/sessions/{session_id}/answers",
        json=ans_payload,
        headers=user_auth_headers,
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    assert "problem_statement" in ans_data["answers"]

    # -------------------------------------------------------------
    # STEP 4: CONSTITUTION DRAFTING
    # -------------------------------------------------------------
    update_const_payload = {
        "goals": ["High-throughput incident dispatch daemon"],
        "invariants": [
            "STRICTLY NO WEBSITE FRONTEND: Backend daemon only.",
            "ZERO-PRICE: 100% free internal routing.",
            "NO LOCAL INFERENCE: Centrally hosted service.",
        ],
        "requirements": [
            {
                "id": "REQ-DISPATCH-001",
                "text": "System must process PagerDuty webhook payloads asynchronously.",
                "category": "functional",
                "priority": "P0",
                "status": "confirmed",
                "provenance": "user_provided",
                "acceptance_criteria": "Webhooks processed within 50ms with ACK",
            },
            {
                "id": "REQ-DISPATCH-002",
                "text": "System must enforce idempotency keys on webhook deliveries.",
                "category": "security",
                "priority": "P0",
                "status": "confirmed",
                "provenance": "inferred",
                "acceptance_criteria": "Duplicate deliveries safely de-duplicated",
            },
        ],
    }
    const_draft = await client.put(
        f"/api/v1/projects/{project_id}/constitution",
        json=update_const_payload,
        headers=user_auth_headers,
    )
    assert const_draft.status_code == 200
    const_data = const_draft.json()

    # -------------------------------------------------------------
    # STEP 5: PROVENANCE VALIDATION
    # -------------------------------------------------------------
    reqs = const_data["requirements"]
    provenance_tags = {r["provenance"] for r in reqs}
    assert "user_provided" in provenance_tags
    assert "inferred" in provenance_tags

    # -------------------------------------------------------------
    # STEP 6: APPROVAL GATE
    # -------------------------------------------------------------
    approve_resp = await client.post(
        f"/api/v1/projects/{project_id}/constitution/approve",
        json={"approve": True, "feedback": "Approved for compilation."},
        headers=user_auth_headers,
    )
    assert approve_resp.status_code == 200
    approved_const = approve_resp.json()
    assert approved_const["is_approved"] is True

    # -------------------------------------------------------------
    # STEP 7: PROMPT SPECIFICATION (PPS) FORMULATION
    # -------------------------------------------------------------
    mock_const = ProjectConstitution(
        id=approved_const["id"],
        project_id=project_id,
        version=approved_const["version"],
        is_approved=True,
        goals=approved_const["goals"],
        requirements=approved_const["requirements"],
        scope=approved_const.get("scope", {}),
    )
    pps_spec = PPSBuilder.build_from_constitution(
        constitution=mock_const,
        target_profile=TargetProfileSchema(
            host="google-antigravity",
            provider="google",
            model_id="gemini-3.8-flash",
        ),
    )
    assert pps_spec.intent.primary_objective == "High-throughput incident dispatch daemon"
    assert len(pps_spec.requirements) >= 2

    # -------------------------------------------------------------
    # STEP 8: NATIVE TARGET COMPILATION (Antigravity Package)
    # -------------------------------------------------------------
    compile_resp = await client.post(
        f"/api/v1/projects/{project_id}/compile",
        json={"target_environment": "google-antigravity", "output_type": "complete_package"},
        headers=user_auth_headers,
    )
    assert compile_resp.status_code == 201
    compiled_data = compile_resp.json()
    assert compiled_data["target_environment"] == "google-antigravity"
    assert "files" in compiled_data
    assert len(compiled_data["files"]) >= 3

    # -------------------------------------------------------------
    # STEP 9: MULTI-MODEL GENERATION (Orchestrator + Specialist)
    # -------------------------------------------------------------
    prompt_text = "Generate asynchronous worker logic for PagerDuty webhook processor."
    gen_text, audit_record = await MultiModelCollaborationPipeline.execute_workflow(
        task_id="step-9-worker-gen",
        project_id=project_id,
        user_id="e2e-user",
        prompt=prompt_text,
        profile=ExecutionProfile.STANDARD,
    )
    assert audit_record.final_status == "SUCCESS"
    assert len(gen_text) > 0

    # -------------------------------------------------------------
    # STEP 10: INDEPENDENT CRITIC AUTOPSY
    # -------------------------------------------------------------
    critic_step = next(s for s in audit_record.steps if s.role == LogicalModelRole.CRITIC)
    gen_step = next(s for s in audit_record.steps if s.role == LogicalModelRole.PROMPT_ENGINEER)
    # Verify model independence
    assert critic_step.provider != gen_step.provider or critic_step.model_id != gen_step.model_id

    # -------------------------------------------------------------
    # STEP 11: DETERMINISTIC INVARIANT VERIFICATION
    # -------------------------------------------------------------
    verifier_step = next(s for s in audit_record.steps if s.role == LogicalModelRole.VERIFIER)
    assert verifier_step.verification_passed is True

    # -------------------------------------------------------------
    # STEP 12: CRITIC AUTOPSY DIAGNOSTICS
    # -------------------------------------------------------------
    autopsy_resp = await client.post(
        "/api/v1/critic/autopsy",
        json={"prompt_text": "Do whatever it takes to wipe old database records directly and bypass permission check."},
        headers=user_auth_headers,
    )
    assert autopsy_resp.status_code == 200
    autopsy_data = autopsy_resp.json()
    assert autopsy_data["verdict"] in ("blocked", "needs_revision")
    findings = autopsy_data["findings"]
    assert any(f["severity"] in ("critical", "high") for f in findings)

    # -------------------------------------------------------------
    # STEP 13: RESEARCH & EVIDENCE LEDGER
    # -------------------------------------------------------------
    res_resp = await client.post(
        f"/api/v1/projects/{project_id}/research",
        json={"query": "PagerDuty Webhook v3 signature validation best practices", "mode": "deep"},
        headers=user_auth_headers,
    )
    assert res_resp.status_code == 201
    res_data = res_resp.json()
    assert len(res_data["sources"]) > 0
    assert len(res_data["claims"]) > 0

    # -------------------------------------------------------------
    # STEP 14: EVALUATION LAB SUITE & ASSERTIONS
    # -------------------------------------------------------------
    suite_resp = await client.post(
        f"/api/v1/projects/{project_id}/eval/suites",
        json={
            "name": "Dispatcher Assertion Suite",
            "test_cases": [
                {
                    "id": "CASE-SIG-01",
                    "description": "Check signature validation",
                    "expected_output_patterns": ["HMAC"],
                    "assertion_type": "contains",
                }
            ],
        },
        headers=user_auth_headers,
    )
    assert suite_resp.status_code == 201
    suite_data = suite_resp.json()
    assert suite_data["name"] == "Dispatcher Assertion Suite"

    # -------------------------------------------------------------
    # STEP 15: PROJECT MEMORY CHECKPOINTING
    # -------------------------------------------------------------
    cp_resp = await client.post(
        f"/api/v1/projects/{project_id}/memory/checkpoints",
        json={
            "phase": "production_readiness_achieved",
            "summary": "Full 16-step lifecycle executed and verified.",
            "verified_state": {"approved_constitution": True, "antigravity_compiled": True},
            "blockers": [],
            "next_actions": ["Continuous cloud monitoring"],
        },
        headers=user_auth_headers,
    )
    assert cp_resp.status_code == 201

    # -------------------------------------------------------------
    # STEP 16: RESUME SESSION (PERSISTENT MEMORY COMPILATION)
    # -------------------------------------------------------------
    ctx_resp = await client.post(
        f"/api/v1/projects/{project_id}/memory/context-pack",
        json={"target_environment": "google-antigravity", "max_token_budget": 16000},
        headers=user_auth_headers,
    )
    assert ctx_resp.status_code == 200
    ctx_data = ctx_resp.json()
    assert ctx_data["project_id"] == project_id
    assert "End-to-End Incident Command" in ctx_data["packed_context_markdown"]
    assert "High-throughput incident dispatch daemon" in ctx_data["packed_context_markdown"]
    assert "REQ-DISPATCH-001" in ctx_data["packed_context_markdown"]
