"""Independent Acceptance Trace Validator negative tests.

Verifies all 21 failure modes from Phase P / Section 19:
1. Invalid scenario ID
2. Duplicate scenario IDs
3. Missing artifact bindings in completed scenario
4. Incorrect artifact SHA-256 hash
5. Wrong artifact byte size (<= 0)
6. Orphan resolution event (missing finding_id)
7. False resolution (finding marked resolved in events but pending in active ledger)
8. Missing required warning (unresolved finding omitted from warnings in COMPLETED_WITH_WARNINGS)
9. Orphan warning / count mismatch between warning strings and records
10. Historical initial autopsy snapshot mutation
11. Invalid state transition
12. Terminal state mismatch (current_state != terminal_state)
13. Missing step timestamps (started_at or completed_at)
14. Impossible timestamp order (completed_at < started_at or negative duration)
15. Missing mandatory criterion evidence in terminal success
16. Unsupported prose-only evidence for mandatory criterion
17. Mock model labeled live
18. Replayed provider call labeled fresh live execution
19. Simulated research labeled live search
20. Unauthorized cross-tenant artifact access
21. Final autopsy evaluated on incorrect/obsolete artifact version
"""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from promptiq.acceptance.validator import AcceptanceTraceValidator


@pytest.fixture
def base_valid_trace() -> dict[str, Any]:
    """Loads a minimal valid trace object based on Trace V4."""
    trace_path = Path("docs/ACCEPTANCE_SCENARIOS_TRACE_V4.json")
    if trace_path.exists():
        with open(trace_path, encoding="utf-8") as f:
            data = json.load(f)
            # Use only scenario 1 as minimal fixture
            return {
                "runner_version": data.get("runner_version", "4.0.0"),
                "scenarios": [copy.deepcopy(data["scenarios"][0])],
            }
    # Fallback minimal valid scenario
    return {
        "runner_version": "4.0.0",
        "scenarios": [
            {
                "scenario_id": "scenario_test_valid",
                "category": "software_engineering",
                "current_state": "SUCCESS_FULLY_VERIFIED",
                "terminal_state": "SUCCESS_FULLY_VERIFIED",
                "steps": [
                    {
                        "step_name": "step_1",
                        "state": "STEP_EXECUTED",
                        "started_at": "2026-11-22T00:00:00.000000+00:00",
                        "completed_at": "2026-11-22T00:00:01.000000+00:00",
                        "duration_ms": 1000.0,
                    }
                ],
                "transitions": [
                    {
                        "transition_id": "tr-1",
                        "from_state": "STEP_EXECUTED",
                        "to_state": "STEP_VALIDATED",
                    },
                    {
                        "transition_id": "tr-2",
                        "from_state": "STEP_VALIDATED",
                        "to_state": "SUCCESS_FULLY_VERIFIED",
                    },
                ],
                "acceptance_criteria": [
                    {
                        "id": "TC-AC-1",
                        "description": "Valid criterion",
                        "is_mandatory": True,
                        "satisfied": True,
                        "evidence": "Artifact SHA-256 verified: abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
                        "evidence_reference": "ref-1",
                    }
                ],
                "artifact_bindings": [
                    {
                        "artifact_id": "art-1",
                        "content_hash": "a" * 64,
                        "byte_size": 128,
                        "persisted": True,
                        "retrievable": True,
                    }
                ],
                "warnings": [],
                "warning_records": [],
            }
        ],
    }


def test_positive_valid_trace_passes(base_valid_trace):
    """Proves that a completely valid trace passes independent validation with 0 errors."""
    validator = AcceptanceTraceValidator(base_valid_trace)
    report = validator.validate_all()
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.failed_checks == 0


def test_negative_01_invalid_scenario_id(base_valid_trace):
    """Failure Mode 1: Empty or missing scenario_id is rejected."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["scenario_id"] = ""
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "scenario_id" for e in report.errors)


def test_negative_02_duplicate_scenario_ids(base_valid_trace):
    """Failure Mode 2: Duplicate scenario_id across the suite is rejected."""
    trace = copy.deepcopy(base_valid_trace)
    dup = copy.deepcopy(trace["scenarios"][0])
    trace["scenarios"].append(dup)
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "duplicate_id" for e in report.errors)


def test_negative_03_missing_artifacts(base_valid_trace):
    """Failure Mode 3: Completed scenario missing artifact bindings is rejected."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["artifact_bindings"] = []
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "missing_artifacts" for e in report.errors)


def test_negative_04_incorrect_artifact_hash(base_valid_trace):
    """Failure Mode 4: Artifact with non-64 character SHA-256 hash is rejected."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["artifact_bindings"][0]["content_hash"] = "invalid_hash"
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "invalid_artifact_hash" for e in report.errors)


def test_negative_05_wrong_artifact_byte_size(base_valid_trace):
    """Failure Mode 5: Artifact with zero or negative byte size is rejected."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["artifact_bindings"][0]["byte_size"] = 0
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "invalid_artifact_byte_size" for e in report.errors)


def test_negative_06_orphan_resolution_event(base_valid_trace):
    """Failure Mode 6: Resolution event missing finding_id is rejected."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["resolution_events"] = [
        {
            "resolution_id": "res-orphan",
            "finding_id": None,
            "status": "resolved",
            "revised_artifact_hash": "a" * 64,
        }
    ]
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "orphan_resolution_event" for e in report.errors)


def test_negative_07_false_resolution(base_valid_trace):
    """Failure Mode 7: Finding marked resolved in events but pending in active autopsy ledger."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["resolution_events"] = [
        {
            "resolution_id": "res-1",
            "finding_id": "f-123",
            "status": "resolved",
            "revised_artifact_hash": "a" * 64,
        }
    ]
    trace["scenarios"][0]["autopsy_findings"] = [
        {
            "id": "f-123",
            "is_resolved": False,
            "disposition": "pending",
        }
    ]
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "finding_ledger_inconsistency" for e in report.errors)


def test_negative_08_missing_required_warning(base_valid_trace):
    """Failure Mode 8: COMPLETED_WITH_WARNINGS scenario missing warnings array."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["terminal_state"] = "COMPLETED_WITH_WARNINGS"
    trace["scenarios"][0]["current_state"] = "COMPLETED_WITH_WARNINGS"
    trace["scenarios"][0]["warnings"] = []
    trace["scenarios"][0]["unresolved_findings"] = []
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "completed_with_warnings_missing_warnings" for e in report.errors)


def test_negative_09_orphan_warning_count_mismatch(base_valid_trace):
    """Failure Mode 9: Count mismatch between warnings strings and warning_records."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["terminal_state"] = "COMPLETED_WITH_WARNINGS"
    trace["scenarios"][0]["current_state"] = "COMPLETED_WITH_WARNINGS"
    trace["scenarios"][0]["warnings"] = ["Warning 1", "Warning 2"]
    trace["scenarios"][0]["warning_records"] = [{"message": "Warning 1"}]
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "warning_count_mismatch" for e in report.errors)


def test_negative_10_historical_autopsy_mutation(base_valid_trace):
    """Failure Mode 10: Mutating historical initial autopsy snapshot is strictly rejected."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["initial_autopsy"] = {
        "id": "aut-init",
        "findings": [{"id": "f-init", "is_resolved": True}],  # Mutated snapshot
    }
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "historical_autopsy_mutation" for e in report.errors)


def test_negative_11_invalid_state_transition(base_valid_trace):
    """Failure Mode 11: Illegal direct jump across states is rejected."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["transitions"] = [
        {
            "transition_id": "tr-illegal",
            "from_state": "STEP_EXECUTED",
            "to_state": "SUCCESS_FULLY_VERIFIED",  # Illegal bypass of STEP_VALIDATED
        }
    ]
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "illegal_transition" for e in report.errors)


def test_negative_12_terminal_state_mismatch(base_valid_trace):
    """Failure Mode 12: Mismatch between current_state and terminal_state."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["current_state"] = "STEP_VALIDATED"
    trace["scenarios"][0]["terminal_state"] = "SUCCESS_FULLY_VERIFIED"
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "terminal_state_mismatch" for e in report.errors)


def test_negative_13_missing_step_timestamp(base_valid_trace):
    """Failure Mode 13: Step missing started_at or completed_at timestamp."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["steps"][0]["started_at"] = None
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "missing_timestamp" for e in report.errors)


def test_negative_14_impossible_timestamp_order(base_valid_trace):
    """Failure Mode 14: Step completed_at preceding started_at or negative duration."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["steps"][0]["started_at"] = "2026-11-22T00:00:10.000000+00:00"
    trace["scenarios"][0]["steps"][0]["completed_at"] = "2026-11-22T00:00:05.000000+00:00"
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "impossible_timestamp_order" for e in report.errors)


def test_negative_15_missing_mandatory_criterion_evidence(base_valid_trace):
    """Failure Mode 15: Mandatory criterion left unsatisfied in terminal success."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["acceptance_criteria"][0]["satisfied"] = False
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "unsatisfied_mandatory_criterion" for e in report.errors)


def test_negative_16_unsupported_prose_only_evidence(base_valid_trace):
    """Failure Mode 16: Mandatory criterion satisfied with plain prose lacking verifiable token."""
    trace = copy.deepcopy(base_valid_trace)
    crit = trace["scenarios"][0]["acceptance_criteria"][0]
    crit["evidence"] = "Everything is good and looks fine"
    crit["evidence_reference"] = None
    crit["verifiable_data"] = None
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "unsupported_prose_evidence" for e in report.errors)


def test_negative_17_mock_model_labeled_live(base_valid_trace):
    """Failure Mode 17: Mock model illegally labeled LIVE or LIVE_PROVIDER."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["evaluation_records"] = [
        {
            "id": "eval-1",
            "model_id": "promptiq-mock-v1",
            "provider_route": "mock",
            "execution_mode": "LIVE_PROVIDER",
        }
    ]
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "mock_labeled_live" for e in report.errors)


def test_negative_18_replayed_provider_call_labeled_fresh(base_valid_trace):
    """Failure Mode 18: Replayed provider call labeled LIVE without replay provenance."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["evaluation_records"] = [
        {
            "id": "eval-replay",
            "model_id": "groq/gpt-oss-120b",
            "execution_mode": "LIVE",
            "is_replayed": True,
            "replay_provenance_id": None,
        }
    ]
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "replayed_provider_call_labeled_fresh" for e in report.errors)


def test_negative_19_simulated_research_labeled_live(base_valid_trace):
    """Failure Mode 19: Simulated research claim classified as LIVE_SEARCH."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["execution_metadata"] = {
        "research_claims": [
            {
                "id": "claim-fake-live",
                "source_type": "simulated",
                "retrieval_classification": "LIVE_SEARCH",
            }
        ]
    }
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "simulated_research_labeled_live" for e in report.errors)


def test_negative_20_unauthorized_cross_tenant_artifact_access(base_valid_trace):
    """Failure Mode 20: Artifact from another workspace accessed in scenario."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["execution_metadata"] = {"workspace_id": "ws-tenant-alpha"}
    trace["scenarios"][0]["artifact_bindings"][0]["workspace_id"] = "ws-tenant-beta"
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "cross_tenant_artifact_access" for e in report.errors)


def test_negative_21_autopsy_on_incorrect_artifact_version(base_valid_trace):
    """Failure Mode 21: Final autopsy evaluated on obsolete pre-revision artifact hash."""
    trace = copy.deepcopy(base_valid_trace)
    old_hash = "1" * 64
    new_hash = "2" * 64
    trace["scenarios"][0]["revision_events"] = [
        {
            "original_artifact_hash": old_hash,
            "revised_artifact_hash": new_hash,
        }
    ]
    trace["scenarios"][0]["final_autopsy"] = {
        "id": "aut-final-wrong",
        "artifact_hash": old_hash,  # Evaluated old instead of new!
    }
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "autopsy_wrong_artifact_version" for e in report.errors)


def test_negative_22_unresolvable_artifact_hash_in_evidence(base_valid_trace):
    """Failure Mode 22: Mandatory criterion references fabricated artifact hash not in artifact_bindings."""
    trace = copy.deepcopy(base_valid_trace)
    phantom_hash = "f" * 64
    trace["scenarios"][0]["acceptance_criteria"][0]["evidence"] = f"Artifact bound with SHA-256 hash: {phantom_hash}"
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "unresolved_evidence_reference" for e in report.errors)


def test_negative_23_unresolvable_artifact_id_in_evidence(base_valid_trace):
    """Failure Mode 23: Mandatory criterion claims artifact reference ID not in artifact_bindings."""
    trace = copy.deepcopy(base_valid_trace)
    trace["scenarios"][0]["acceptance_criteria"][0]["evidence_record_type"] = "artifact"
    trace["scenarios"][0]["acceptance_criteria"][0]["evidence_reference"] = "phantom-artifact-uuid-999"
    validator = AcceptanceTraceValidator(trace)
    report = validator.validate_all()
    assert report.is_valid is False
    assert any(e.check_name == "unresolved_evidence_reference" for e in report.errors)
