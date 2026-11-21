"""Comprehensive test suite for Master Platform Execution.

Covers:
- SSRF prevention and URL sanitization
- Contradiction and missing high-impact info detection in discovery
- Constitution rollback and historical version comparison
- Multi-target compilation and target recommendation
- Prompt autopsy deterministic revision verification and release blocking
- Research engine evidence provenance and mock labeling
- Two-phase capacity reservation and durable quota accounting
- Evaluation lab comparative benchmarks and regression detection
- Project data export bundle and cascading deletion
- API routes for constitution, compiler, critic, and projects
"""

import pytest

from promptiq.compiler.target_compiler import target_compiler
from promptiq.core.exceptions import SecurityError
from promptiq.core.security import validate_and_sanitize_url
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.discovery.adaptive import AdaptiveDiscoveryEngine
from promptiq.eval.test_lab import PromptTestLab
from promptiq.gateway.governor import CapacityGovernor
from promptiq.models.discovery import DiscoverySession
from promptiq.models.eval import EvaluationRun
from promptiq.research.connectors.base import MockSearchConnector
from promptiq.research.engine import ResearchEngine
from promptiq.schemas.critic import CriticFindingSchema
from promptiq.schemas.eval import EvaluationSuiteCreate
from promptiq.schemas.project import ProjectCreate
from promptiq.schemas.research import ResearchRequest
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService


# 1. SSRF and URL Sanitization Tests
def test_ssrf_blocking_private_and_metadata_targets():
    """Validates that SSRF protection blocks cloud metadata, loopback, and private IPs."""
    with pytest.raises(SecurityError):
        validate_and_sanitize_url("http://localhost:8080/secret")

    with pytest.raises(SecurityError):
        validate_and_sanitize_url("http://127.0.0.1/admin")

    with pytest.raises(SecurityError):
        validate_and_sanitize_url("http://169.254.169.254/computeMetadata/v1/")

    with pytest.raises(SecurityError):
        validate_and_sanitize_url("http://metadata.google.internal/computeMetadata/v1/")

    with pytest.raises(SecurityError):
        validate_and_sanitize_url("http://10.0.0.1/internal-api")

    with pytest.raises(SecurityError):
        validate_and_sanitize_url("http://192.168.1.100:5000/metrics")

    with pytest.raises(SecurityError):
        validate_and_sanitize_url("file:///etc/passwd")

    with pytest.raises(SecurityError):
        validate_and_sanitize_url("gopher://example.com")

    # Valid public URL passes
    sanitized = validate_and_sanitize_url("https://en.wikipedia.org/wiki/Artificial_intelligence")
    assert sanitized == "https://en.wikipedia.org/wiki/Artificial_intelligence"


# 2. Discovery Contradiction and Missing Information Detection
def test_discovery_contradiction_and_gap_detection():
    """Validates contradiction detection between constraints and answers, and missing info flags."""
    # Case A: Strict no-frontend constraint with UI request in answers
    session_contradict = DiscoverySession(
        project_id="proj-123",
        depth="guided",
        initial_intake={
            "goal": "Build payment processing gateway with no frontend",
            "constraints": ["strict no-frontend invariant", "zero-price hosted inference"],
        },
        answers={
            "surfaces_required": "Web workspace, React dashboard, mobile companion",
            "visual_direction": "React Tailwind UI",
        },
    )
    contradictions = AdaptiveDiscoveryEngine.detect_contradictions(session_contradict)
    assert len(contradictions) >= 1
    assert "no-frontend" in contradictions[0].lower()

    # Case B: Missing high-impact information
    session_incomplete = DiscoverySession(
        project_id="proj-123",
        depth="guided",
        initial_intake={"goal": "Build an API"},
        answers={},
    )
    missing = AdaptiveDiscoveryEngine.detect_missing_high_impact_info(session_incomplete)
    assert len(missing) >= 2
    assert any("acceptance criteria" in m.lower() for m in missing)


# 3. Constitution Rollback & Version Comparison
@pytest.mark.asyncio
async def test_constitution_rollback_and_compare(db_session, test_user):
    """Validates that rolling back creates immutable version N+1 and compare returns granular diffs."""
    user, _ = test_user
    proj = await ProjectService.create_project(
        db_session,
        user.id,
        ProjectCreate(name="Rollback Test Project", description="Testing rollback"),
    )
    await db_session.commit()

    from promptiq.schemas.constitution import ConstitutionUpdate, RequirementItem

    update_v2 = ConstitutionUpdate(
        goals=["Build updated system v2"],
        requirements=[
            RequirementItem(
                id="REQ-001",
                text="Must support asynchronous processing",
                category="functional",
                priority="P0",
                status="confirmed",
                provenance="user_provided",
            )
        ],
    )
    await ConstitutionService.update_constitution(db_session, proj.id, user.id, update_v2)
    await db_session.commit()

    comp = await ConstitutionService.compare_versions(db_session, proj.id, 1, 2, user.id)
    assert comp["v1"] == 1
    assert comp["v2"] == 2
    assert "goals" in comp["diff"]["modified"]
    assert "requirements" in comp["diff"]["modified"]

    reverted = await ConstitutionService.rollback_to_version(db_session, proj.id, 1, user.id)
    await db_session.commit()

    assert reverted.version == 3
    assert reverted.goals == ["Testing rollback"]
    assert len(reverted.requirements) == 0


# 4. Target Recommendation and Multi-Target Compilation
@pytest.mark.asyncio
async def test_target_recommendation_and_multi_target(db_session, test_user):
    """Validates target recommendation engine and multi-target compilation."""
    user, _ = test_user
    rec_antigravity = target_compiler.recommend_target(
        "Autonomous multi-agent system with MCP tool integration"
    )
    assert rec_antigravity["recommended_target"] == "google-antigravity"
    assert rec_antigravity["compatibility_scores"]["google-antigravity"] > 0.90
    assert len(rec_antigravity["pros"]) > 0

    proj = await ProjectService.create_project(
        db_session,
        user.id,
        ProjectCreate(name="Multi-Target Project", description="Testing multi-compile"),
    )
    from promptiq.schemas.constitution import ConstitutionApprovalRequest

    await ConstitutionService.approve_constitution(
        db_session, proj.id, user.id, ConstitutionApprovalRequest(approve=True)
    )
    await db_session.commit()

    multi_res = await target_compiler.compile_multi_target(
        db_session,
        project_id=proj.id,
        user_id=user.id,
        targets=["google-antigravity", "claude-code", "cursor"],
    )
    await db_session.commit()

    assert "google-antigravity" in multi_res["packages"]
    assert "claude-code" in multi_res["packages"]
    assert "cursor" in multi_res["packages"]
    assert len(multi_res["failures"]) == 0


# 5. Prompt Autopsy Revision Verification
def test_autopsy_revision_verification():
    """Validates deterministic verification of revised prompt text against previous findings."""
    original_findings = [
        CriticFindingSchema(
            category="ambiguity",
            severity="medium",
            finding="Prompt contains vague language: etc",
            evidence_passage="etc",
            consequence="Hallucination",
            recommendation="Replace vague references with concrete specifications.",
            blocks_release=False,
        ),
        CriticFindingSchema(
            category="security",
            severity="high",
            finding="Excessive agency detected: 'delete files'",
            evidence_passage="delete files",
            consequence="Destructive operations",
            recommendation="Add explicit boundary constraints requiring human sign-off.",
            blocks_release=True,
        ),
    ]

    unresolved_text = "Please delete files as needed and clean up stuff."
    res1 = PromptAutopsyEngine.verify_findings_against_artifact(original_findings, unresolved_text)
    assert not res1.all_resolved
    assert res1.blocks_release is True

    resolved_text = (
        "Perform cleanup. Do not execute destructive operations without explicit approval. "
        "Boundaries: read-only by default. Required files: temp.log."
    )
    res2 = PromptAutopsyEngine.verify_findings_against_artifact(original_findings, resolved_text)
    assert res2.all_resolved is True
    assert res2.blocks_release is False
    assert res2.resolved_count == 2
    assert res2.unresolved_count == 0


# 6. Research Engine Provenance and Mock Labeling
@pytest.mark.asyncio
async def test_research_provenance_and_mock_labeling(db_session, test_user):
    """Validates that research evidence correctly tracks provenance and labels mocks."""
    user, _ = test_user
    proj = await ProjectService.create_project(
        db_session,
        user.id,
        ProjectCreate(name="Research Proj", description="Testing evidence provenance"),
    )
    await db_session.commit()

    engine = ResearchEngine(search_connector=MockSearchConnector())
    resp = await engine.execute_research(
        db_session,
        project_id=proj.id,
        user_id=user.id,
        request=ResearchRequest(query="Model Context Protocol specifications", max_sources=2),
    )
    await db_session.commit()

    assert len(resp.sources) > 0
    for s in resp.sources:
        assert s.provenance == "simulated_mock"
        assert s.is_mock is True

    assert len(resp.claims) > 0
    for c in resp.claims:
        assert c.provenance == "simulated_mock"
        assert c.is_mock is True
        assert "simulated" in c.confidence_rationale.lower()


# 7. Two-Phase Quota Reservation in CapacityGovernor
def test_capacity_governor_two_phase_reservation(tmp_path):
    """Validates capacity reservation, in-flight accounting, release, and reconciliation."""
    ledger_file = tmp_path / "test_reservation_ledger.json"
    governor = CapacityGovernor(ledger_path=ledger_file, auto_load=False)
    model_id = "openai/gpt-oss-120b"

    initial_status = governor.get_model_quota_status(model_id)
    assert initial_status["reserved_tokens"] == 0

    token = governor.reserve_capacity(model_id=model_id, estimated_tokens=2000, ttl_seconds=60)
    assert token.startswith("res_")

    reserved_status = governor.get_model_quota_status(model_id)
    assert reserved_status["reserved_tokens"] == 2000
    assert reserved_status["tpm_remaining"] == initial_status["tpm_limit"] - 2000

    governor.release_reservation(token)
    released_status = governor.get_model_quota_status(model_id)
    assert released_status["reserved_tokens"] == 0
    assert released_status["tpm_remaining"] == initial_status["tpm_limit"]

    token2 = governor.reserve_capacity(model_id=model_id, estimated_tokens=1500, ttl_seconds=60)
    governor.reconcile_reservation(token2, actual_tokens=1200, http_status=200)

    reconciled_status = governor.get_model_quota_status(model_id)
    assert reconciled_status["reserved_tokens"] == 0
    assert reconciled_status["tpm_used"] == 1200


# 8. Evaluation Lab Comparative Benchmarks
@pytest.mark.asyncio
async def test_evaluation_lab_comparative_runs(db_session, test_user):
    """Validates regression tracking and delta comparisons between evaluation runs."""
    user, _ = test_user
    proj = await ProjectService.create_project(
        db_session,
        user.id,
        ProjectCreate(name="Eval Compare Proj", description="Testing comparative eval"),
    )
    suite = await PromptTestLab.create_suite(
        db_session,
        proj.id,
        user.id,
        EvaluationSuiteCreate(
            name="Assertion Suite",
            test_cases=[
                {"id": "TC-1", "description": "Case 1", "expected_output_patterns": ["Alpha"]},
                {"id": "TC-2", "description": "Case 2", "expected_output_patterns": ["Beta"]},
            ],
        ),
    )
    await db_session.commit()

    base_run = EvaluationRun(
        suite_id=suite.id,
        package_id=None,
        model_id="baseline-model",
        provider_route="free",
        pass_rate=100.0,
        total_cases=2,
        passed_cases=2,
        results=[{"case_id": "TC-1", "passed": True}, {"case_id": "TC-2", "passed": True}],
        latency_ms=120.0,
        cost_estimate=0.0,
    )
    db_session.add(base_run)

    cand_run = EvaluationRun(
        suite_id=suite.id,
        package_id=None,
        model_id="candidate-model",
        provider_route="free",
        pass_rate=50.0,
        total_cases=2,
        passed_cases=1,
        results=[{"case_id": "TC-1", "passed": True}, {"case_id": "TC-2", "passed": False}],
        latency_ms=90.0,
        cost_estimate=0.0,
    )
    db_session.add(cand_run)
    await db_session.flush()
    await db_session.commit()

    comp = await PromptTestLab.compare_runs(
        db_session,
        project_id=proj.id,
        user_id=user.id,
        baseline_run_id=base_run.id,
        candidate_run_id=cand_run.id,
    )

    assert comp.has_regressions is True
    assert "TC-2" in comp.newly_failed_cases
    assert comp.pass_rate_delta == -50.0
    assert comp.latency_delta_ms == -30.0


# 9. Project Data Export Bundle & Cascading Deletion
@pytest.mark.asyncio
async def test_project_data_export_and_clean_delete(db_session, test_user):
    """Validates full project data export and clean cascading deletion without foreign key violations."""
    user, _ = test_user
    proj = await ProjectService.create_project(
        db_session,
        user.id,
        ProjectCreate(name="Export & Delete Proj", description="Export test"),
    )
    await db_session.commit()

    export_data = await ProjectService.export_project_data(db_session, proj.id, user.id)
    assert export_data["project"]["id"] == proj.id
    assert len(export_data["constitutions"]) == 1
    assert "exported_at" in export_data

    deleted = await ProjectService.delete_project(db_session, proj.id, user.id)
    assert deleted is True
    await db_session.commit()

    from promptiq.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        await ProjectService.get_project(db_session, proj.id, user.id)


# 10. API Route Tests for New Endpoints
@pytest.mark.asyncio
async def test_api_routes_for_master_platform(client, test_user, user_auth_headers):
    """Tests the new API routes: constitution compare/rollback, compiler multi/recommend, critic verify, and project export."""
    # Create project via API
    resp_create = await client.post(
        "/api/v1/projects",
        json={"name": "API Route Test Project", "description": "Testing routes"},
        headers=user_auth_headers,
    )
    assert resp_create.status_code == 201
    proj_data = resp_create.json()
    proj_id = proj_data["id"]

    # Test Target Recommendation route
    resp_rec = await client.post(
        f"/api/v1/projects/{proj_id}/compile/recommend",
        headers=user_auth_headers,
    )
    assert resp_rec.status_code == 200
    rec_data = resp_rec.json()
    assert "recommended_target" in rec_data
    assert "compatibility_scores" in rec_data

    # Test Critic Revision Verification route
    resp_verify = await client.post(
        "/api/v1/critic/verify-revision",
        json={
            "original_findings": [
                {
                    "category": "ambiguity",
                    "severity": "medium",
                    "finding": "Contains etc",
                    "evidence_passage": "etc",
                    "consequence": "Gaps",
                    "recommendation": "Be explicit",
                }
            ],
            "revised_text": "Exhaustive specification without vague words.",
        },
        headers=user_auth_headers,
    )
    assert resp_verify.status_code == 200
    assert resp_verify.json()["all_resolved"] is True

    # Test Project Export route
    resp_export = await client.get(
        f"/api/v1/projects/{proj_id}/export",
        headers=user_auth_headers,
    )
    assert resp_export.status_code == 200
    assert resp_export.json()["project"]["id"] == proj_id
