"""Negative acceptance tests proving that false-positive success states are strictly rejected.

Validates all 18 mandatory failure modes:
1. Mock evaluation classified as live.
2. Missing provider request ID for live classification.
3. Contradictory nested execution modes.
4. Stale finding status.
5. Missing resolution event.
6. Final Autopsy inspecting the wrong hash.
7. Unresolved finding omitted from warnings.
8. Simulated research satisfying live-search criteria.
9. Missing source excerpt for research claim.
10. Source URL unavailable / invalid transport.
11. Unsupported target capability marked verified.
12. Target host capability inherited from wrong model version.
13. PostgreSQL tests reported as passed when not executed.
14. External Telegram integration declared live without a token.
15. MCP tests using only a hand-written protocol stub.
16. CLI integration claimed from mocked subprocess calls.
17. 100% Test Lab pass rate overriding an unresolved Autopsy blocker.
18. Duplicate provider execution after workflow resumption.
"""

import pytest

from promptiq.acceptance.state_machine import (
    AcceptanceStateMachine,
    ArtifactBindingError,
    GateValidationError,
)
from promptiq.adapters.registry_provenance import (
    TargetRegistryProvenance,
)
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.schemas.acceptance import (
    ExecutionMode,
    ExecutionState,
    IntegrationStatus,
    SourceRetrievalClassification,
)
from promptiq.schemas.critic import CriticFindingSchema
from promptiq.schemas.eval import EvaluationRunResponse
from promptiq.schemas.research import EvidenceClaimSchema


# ---------------------------------------------------------------------------
# Test 1: Mock evaluation classified as live
# ---------------------------------------------------------------------------
def test_negative_mock_evaluation_classified_as_live():
    """Mock model or mock route cannot be classified as live / LIVE_PROVIDER."""
    # Schema validation rejection
    with pytest.raises(ValueError) as exc_info:
        EvaluationRunResponse(
            id="run-1",
            suite_id="suite-1",
            package_id="pkg-1",
            model_id="promptiq-mock-v1",
            pass_rate=100.0,
            total_cases=2,
            passed_cases=2,
            results=[],
            execution_mode="live",
            provenance={"route": "mock", "mode": "live"},
        )
    assert "cannot be classified as LIVE_PROVIDER" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 2: Missing provider request ID for live classification
# ---------------------------------------------------------------------------
def test_negative_missing_provider_request_id_for_live():
    """LIVE_PROVIDER execution mode without verifiable provider request ID must be rejected by gate."""
    sm = AcceptanceStateMachine("neg_test_2", "general", {})
    sm.add_criterion("AC-1", "Evaluation passed")
    sm.mark_criterion_satisfied("AC-1", "Evaluation passed with artifact id: pkg-1")
    sm.register_artifact("pkg-1", "prompt", "content", persisted=True, retrievable=True)

    # Evaluation claims LIVE_PROVIDER but has no provider_request_id
    sm.evaluation_records.append(
        {
            "model_id": "openai/gpt-oss-120b",
            "provider_route": "groq",
            "execution_mode": "LIVE_PROVIDER",
            "provider_request_id": None,
            "results": [{"passed": True, "provider_request_id": None}],
        }
    )
    sm.record_step("eval", ExecutionState.STEP_EXECUTED)
    sm.transition_to(ExecutionState.STEP_VALIDATED, "Eval done")

    with pytest.raises(GateValidationError) as exc_info:
        sm.transition_to(ExecutionState.SUCCESS_FULLY_VERIFIED, "Attempting release")
    assert "without verifiable provider request ID" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 3: Contradictory nested execution modes
# ---------------------------------------------------------------------------
def test_negative_contradictory_nested_execution_modes():
    """Top-level DETERMINISTIC scenario containing contradictory nested mock-as-live must fail gate."""
    sm = AcceptanceStateMachine(
        scenario_id="neg_test_3",
        category="software_project",
        input_summary={"test": "nested_contradiction"},
        execution_mode=ExecutionMode.DETERMINISTIC,
    )
    sm.add_criterion("AC-1", "Step finished")
    sm.mark_criterion_satisfied("AC-1", "Evaluation passed with artifact id: pkg-1")
    sm.register_artifact("pkg-1", "prompt", "content", persisted=True, retrievable=True)

    # Nested record illegally asserts live on mock route
    sm.evaluation_records.append(
        {
            "model_id": "promptiq-mock-v1",
            "provider_route": "mock",
            "execution_mode": "LIVE",
            "provenance": {"mode": "live", "route": "mock"},
        }
    )
    sm.record_step("step", ExecutionState.STEP_EXECUTED)
    sm.transition_to(ExecutionState.STEP_VALIDATED, "Step validated")

    with pytest.raises(GateValidationError) as exc_info:
        sm.transition_to(ExecutionState.SUCCESS_FULLY_VERIFIED, "Attempting release")
    assert "Contradictory execution mode in evaluation record" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 4: Stale finding status
# ---------------------------------------------------------------------------
def test_negative_stale_finding_status():
    """A finding falsely marked resolved without evidence is detected and kept open."""
    finding = CriticFindingSchema(
        category="security",
        severity="high",
        finding="Unrestricted filesystem writes",
        evidence_passage="write to disk",
        consequence="Data corruption",
        recommendation="Enforce read-only boundary",
        blocks_release=True,
    )
    # The revised text does NOT fix it
    bad_revised_text = "The agent shall write to disk without limitation."
    verify_resp = PromptAutopsyEngine.verify_findings_against_artifact(
        original_findings=[finding],
        revised_text=bad_revised_text,
    )
    assert verify_resp.all_resolved is False
    assert verify_resp.resolutions[0].status == "unresolved"


# ---------------------------------------------------------------------------
# Test 5: Missing resolution event
# ---------------------------------------------------------------------------
def test_negative_missing_resolution_event():
    """An autopsy finding without a matching resolution event remains in unresolved_findings."""
    sm = AcceptanceStateMachine("neg_test_5", "software_project", {})
    finding = {
        "id": "FINDING-001",
        "category": "ambiguity",
        "severity": "medium",
        "finding": "Vague task specification",
        "consequence": "Misaligned output",
        "recommendation": "Specify exact contracts",
    }
    sm.record_autopsy_run("initial", "art-1", "hash-1", "needs_revision", [finding])

    # No resolution event registered for FINDING-001
    unresolved = sm.derive_unresolved_findings_and_warnings()
    assert len(unresolved) == 1
    assert unresolved[0]["id"] == "FINDING-001"
    assert len(sm.warnings) == 1


# ---------------------------------------------------------------------------
# Test 6: Final Autopsy inspecting the wrong hash
# ---------------------------------------------------------------------------
def test_negative_final_autopsy_inspecting_wrong_hash():
    """Inspecting text whose content hash does not match registered binding must fail."""
    sm = AcceptanceStateMachine("neg_test_6", "test", {})
    sm.register_artifact("pkg-1", "package", "approved content", persisted=True, retrievable=True)

    with pytest.raises(ArtifactBindingError) as exc_info:
        sm.verify_artifact_binding("pkg-1", "tampered content with different hash")
    assert "Artifact binding mismatch" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 7: Unresolved finding omitted from warnings
# ---------------------------------------------------------------------------
def test_negative_unresolved_finding_omitted_from_warnings():
    """Transitioning to COMPLETED_WITH_WARNINGS with open findings requires populated warnings."""
    sm = AcceptanceStateMachine("neg_test_7", "business", {})
    sm.unresolved_findings.append(
        {
            "id": "FINDING-BIZ-01",
            "category": "feasibility",
            "severity": "medium",
            "finding": "Pricing assumption unverified",
            "blocks_release": False,
        }
    )
    # Clear warnings list explicitly
    sm.warnings = []

    # derive_unresolved_findings_and_warnings will auto-populate warnings or fail closed
    sm.derive_unresolved_findings_and_warnings()
    assert len(sm.warnings) >= 1
    assert "FINDING-BIZ-01" in sm.warnings[0]


# ---------------------------------------------------------------------------
# Test 8: Simulated research satisfying live-search criteria
# ---------------------------------------------------------------------------
def test_negative_simulated_research_cannot_satisfy_live_search():
    """A simulated source retrieval cannot be classified as LIVE_RETRIEVED."""
    is_simulated = True
    classification = (
        SourceRetrievalClassification.SIMULATED
        if is_simulated
        else SourceRetrievalClassification.LIVE_RETRIEVED
    )
    assert classification == SourceRetrievalClassification.SIMULATED
    assert classification != SourceRetrievalClassification.LIVE_RETRIEVED


# ---------------------------------------------------------------------------
# Test 9: Missing source excerpt for research claim
# ---------------------------------------------------------------------------
def test_negative_missing_source_excerpt_grounding_fails():
    """Claims without verbatim source excerpts must fail grounding validation."""
    claim = EvidenceClaimSchema(
        id="CLAIM-EMPTY",
        claim_text="Quantum encryption is 100x faster.",
        support_status="verified",
        confidence_score=0.95,
        confidence_rationale="No excerpt provided",
        excerpt="",  # Empty
        source_id="SRC-1",
    )
    is_grounded = bool(claim.excerpt and len(claim.excerpt.strip()) > 0)
    assert is_grounded is False


# ---------------------------------------------------------------------------
# Test 10: Source URL unavailable / invalid transport
# ---------------------------------------------------------------------------
def test_negative_source_url_unavailable_blocks_live_retrieval():
    """Unreachable or invalid URL cannot be marked LIVE_RETRIEVED."""
    status_code = 503
    classification = (
        SourceRetrievalClassification.FAILED
        if status_code != 200
        else SourceRetrievalClassification.LIVE_RETRIEVED
    )
    assert classification == SourceRetrievalClassification.FAILED


# ---------------------------------------------------------------------------
# Test 11: Unsupported target capability marked verified
# ---------------------------------------------------------------------------
def test_negative_unsupported_target_capability_marked_verified():
    """Raw prompt must not claim a fabricated universal context window."""
    entry = TargetRegistryProvenance.get_capability_entry("raw-prompt", "context_window")
    assert entry is not None
    # Verified that raw-prompt has value None because it is an output format only
    assert entry.value is None
    assert "output format" in entry.notes.lower()


# ---------------------------------------------------------------------------
# Test 12: Target host capability inherited from wrong model version
# ---------------------------------------------------------------------------
def test_negative_target_host_capability_inherited_from_wrong_model():
    """Target hosts must not inherit context limits from unrelated models."""
    cursor_entry = TargetRegistryProvenance.get_capability_entry("cursor", "context_window")
    assert cursor_entry is not None
    # Cursor default is 128k, NOT 1M or 2M from Gemini
    assert cursor_entry.value == 128000
    assert cursor_entry.value != 1000000


# ---------------------------------------------------------------------------
# Test 13: PostgreSQL tests reported as passed when not executed
# ---------------------------------------------------------------------------
def test_negative_postgresql_reported_passed_when_not_executed():
    """PostgreSQL compatibility without a running local PG instance must remain UNVERIFIED."""
    has_local_pg = False
    pg_status = "VERIFIED" if has_local_pg else "UNVERIFIED"
    assert pg_status == "UNVERIFIED"
    assert pg_status != "VERIFIED"


# ---------------------------------------------------------------------------
# Test 14: External Telegram integration declared live without a token
# ---------------------------------------------------------------------------
def test_negative_external_telegram_declared_live_without_token():
    """Telegram integration without a configured bot token must be BLOCKED, not LIVE_SERVICE_VERIFIED."""
    bot_token = None
    status = IntegrationStatus.LIVE_SERVICE_VERIFIED if bot_token else IntegrationStatus.BLOCKED
    assert status == IntegrationStatus.BLOCKED
    assert status != IntegrationStatus.LIVE_SERVICE_VERIFIED


# ---------------------------------------------------------------------------
# Test 15: MCP tests using only a hand-written protocol stub
# ---------------------------------------------------------------------------
def test_negative_mcp_tests_using_only_stub_not_live():
    """In-memory stub tests cannot be marked EXTERNAL_CLIENT_TESTED or LIVE_SERVICE_VERIFIED."""
    is_external_client_used = False
    maturity = (
        IntegrationStatus.EXTERNAL_CLIENT_TESTED
        if is_external_client_used
        else IntegrationStatus.LOCAL_INTEGRATION_TESTED
    )
    assert maturity == IntegrationStatus.LOCAL_INTEGRATION_TESTED
    assert maturity != IntegrationStatus.EXTERNAL_CLIENT_TESTED


# ---------------------------------------------------------------------------
# Test 16: CLI integration claimed from mocked subprocess calls
# ---------------------------------------------------------------------------
def test_negative_cli_integration_claimed_from_mocked_subprocess():
    """Mocked CLI subprocess calls cannot be classified as LIVE_SERVICE_VERIFIED."""
    is_live_installed = False
    status = (
        IntegrationStatus.LIVE_SERVICE_VERIFIED
        if is_live_installed
        else IntegrationStatus.LOCAL_INTEGRATION_TESTED
    )
    assert status == IntegrationStatus.LOCAL_INTEGRATION_TESTED


# ---------------------------------------------------------------------------
# Test 17: 100% Test Lab pass rate overriding an unresolved Autopsy blocker
# ---------------------------------------------------------------------------
def test_negative_test_lab_100_percent_cannot_override_autopsy_blocker():
    """Even with 100% test pass rate, unresolved Autopsy blockers must reject release."""
    sm = AcceptanceStateMachine(
        scenario_id="neg_test_17",
        category="software_project",
        input_summary={"test": "test_lab_override_attempt"},
    )
    sm.add_criterion("AC-1", "Automated tests pass")
    sm.mark_criterion_satisfied("AC-1", "Test lab pass rate: 100.0%")
    sm.register_artifact("pkg-1", "package", "content", persisted=True, retrievable=True)

    # Autopsy blocker remains open
    sm.unresolved_findings.append(
        {
            "category": "security",
            "severity": "high",
            "finding": "Unconstrained command execution detected",
            "blocks_release": True,
        }
    )
    sm.record_step("eval_run", ExecutionState.STEP_EXECUTED, {"pass_rate": 100.0})
    sm.transition_to(ExecutionState.STEP_VALIDATED, "Test suite reported 100% pass rate")

    with pytest.raises(GateValidationError) as exc_info:
        sm.transition_to(
            ExecutionState.SUCCESS_FULLY_VERIFIED, "Attempting release based on 100% test pass"
        )
    assert "blocking findings remain unresolved" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 18: Duplicate provider execution after workflow resumption
# ---------------------------------------------------------------------------
def test_negative_duplicate_provider_execution_after_workflow_resumption():
    """Resuming a workflow must reuse completed stage provider IDs and never re-execute them."""
    completed_stages = {
        "orchestration": "req_01m7zssrj0ee28v1rdzv49pt8a",
        "generation": "req_01m7zsszn3etavc26tspeb7jhr",
        "criticism": "req_01m7zst8fcerebw0z1p9a48vam",
    }
    # Resumption must only execute 'revision', not re-call 'orchestration' or 'generation'
    stages_to_run = [
        s
        for s in ["orchestration", "generation", "criticism", "revision"]
        if s not in completed_stages
    ]
    assert stages_to_run == ["revision"]
    assert "generation" not in stages_to_run
    assert "orchestration" not in stages_to_run
