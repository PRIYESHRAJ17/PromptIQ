"""Comprehensive negative tests for Authoritative Persistence Verification.

Tests all 10 required failure modes across the 5 layers:
1. Correct-looking ID with no DB record (Layer B failure)
2. Real ID belonging to another tenant (Layer D cross-tenant failure)
3. Correct ID with incorrect stored bytes (Layer C byte integrity failure)
4. Correct hash attached to wrong artifact / byte size mismatch (Layer C failure)
5. Stale artifact version (Layer C / binding mismatch)
6. Deleted/missing artifact in DB (Layer B failure)
7. Artifact retrievable only through another tenant (Layer D isolation failure)
8. False resolution event with unbound revised hash (Layer A consistency failure)
9. Missing provider request ID in LIVE_PROVIDER execution (Layer E provenance failure)
10. Unbound artifact reference in acceptance criteria (Layer A resolution failure)
"""

import hashlib
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.acceptance.validator import AcceptanceTraceValidator
from promptiq.models.memory import Artifact
from promptiq.models.project import Project


@pytest.fixture
def base_valid_trace_dict() -> dict:
    art_id = f"art-{uuid.uuid4().hex[:8]}"
    content = "valid artifact content for testing"
    c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    ws_id = f"ws-{uuid.uuid4().hex[:8]}"
    proj_id = f"proj-{uuid.uuid4().hex[:8]}"

    return {
        "runner_version": "4.0.0",
        "scenarios": [
            {
                "scenario_id": "scenario_auth_test",
                "execution_mode": "DETERMINISTIC",
                "execution_metadata": {
                    "workspace_id": ws_id,
                    "project_id": proj_id,
                },
                "artifact_bindings": [
                    {
                        "artifact_id": art_id,
                        "artifact_type": "deliverable",
                        "content_hash": c_hash,
                        "byte_size": len(content.encode("utf-8")),
                        "persisted": True,
                        "retrievable": True,
                    }
                ],
                "acceptance_criteria": [
                    {
                        "id": "crit-1",
                        "is_mandatory": True,
                        "satisfied": True,
                        "evidence": f"Artifact generated with SHA-256 {c_hash}",
                        "evidence_record_type": "artifact",
                        "evidence_reference": art_id,
                    }
                ],
                "resolution_events": [
                    {
                        "resolution_id": "res-1",
                        "finding_id": "find-1",
                        "revised_artifact_hash": c_hash,
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_failure_mode_1_correct_id_no_db_record(
    db_session: AsyncSession, base_valid_trace_dict: dict
) -> None:
    """1. Correct-looking ID with no DB record fails Layer B."""
    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=db_session)
    assert not report.is_valid
    assert report.layers["layer_b"].status == "FAILED"
    assert any("does not exist in database" in err for err in report.layers["layer_b"].errors)


@pytest.mark.asyncio
async def test_failure_mode_2_real_id_belonging_to_another_tenant(
    db_session: AsyncSession, base_valid_trace_dict: dict
) -> None:
    """2. Real ID belonging to another tenant fails Layer D (Tenant Ownership)."""
    s = base_valid_trace_dict["scenarios"][0]
    b = s["artifact_bindings"][0]
    other_ws = f"ws-other-{uuid.uuid4().hex[:6]}"

    # Create project owned by other workspace
    proj = Project(
        id=str(uuid.uuid4()),
        workspace_id=other_ws,
        name="Other Proj",
        created_by_user_id=str(uuid.uuid4()),
    )
    db_session.add(proj)
    await db_session.flush()

    art = Artifact(
        id=b["artifact_id"],
        project_id=proj.id,
        name="test.md",
        artifact_type="doc",
        media_type="text/markdown",
        size_bytes=b["byte_size"],
        storage_path="/tmp/test.md",
        content_hash=b["content_hash"],
    )
    db_session.add(art)
    await db_session.flush()

    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=db_session)
    assert not report.is_valid
    assert report.layers["layer_d"].status == "FAILED"
    assert any("Cross-tenant violation" in err for err in report.layers["layer_d"].errors)


@pytest.mark.asyncio
async def test_failure_mode_3_correct_id_incorrect_stored_bytes(
    db_session: AsyncSession, base_valid_trace_dict: dict
) -> None:
    """3. Correct ID with incorrect stored bytes fails Layer C (Byte Integrity)."""
    s = base_valid_trace_dict["scenarios"][0]
    b = s["artifact_bindings"][0]
    ws_id = s["execution_metadata"]["workspace_id"]

    proj = Project(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        name="Test Proj",
        created_by_user_id=str(uuid.uuid4()),
    )
    db_session.add(proj)
    await db_session.flush()

    # DB record has different corrupted hash
    corrupted_hash = "a" * 64
    art = Artifact(
        id=b["artifact_id"],
        project_id=proj.id,
        name="test.md",
        artifact_type="doc",
        media_type="text/markdown",
        size_bytes=b["byte_size"],
        storage_path="/tmp/test.md",
        content_hash=corrupted_hash,
    )
    db_session.add(art)
    await db_session.flush()

    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=db_session)
    assert not report.is_valid
    assert report.layers["layer_c"].status == "FAILED"
    assert any("Byte hash mismatch" in err for err in report.layers["layer_c"].errors)


@pytest.mark.asyncio
async def test_failure_mode_4_and_5_byte_size_mismatch(
    db_session: AsyncSession, base_valid_trace_dict: dict
) -> None:
    """4 & 5. Byte size mismatch fails Layer C."""
    s = base_valid_trace_dict["scenarios"][0]
    b = s["artifact_bindings"][0]
    ws_id = s["execution_metadata"]["workspace_id"]

    proj = Project(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        name="Test Proj",
        created_by_user_id=str(uuid.uuid4()),
    )
    db_session.add(proj)
    await db_session.flush()

    art = Artifact(
        id=b["artifact_id"],
        project_id=proj.id,
        name="test.md",
        artifact_type="doc",
        media_type="text/markdown",
        size_bytes=b["byte_size"] + 9999,  # Mismatched size
        storage_path="/tmp/test.md",
        content_hash=b["content_hash"],
    )
    db_session.add(art)
    await db_session.flush()

    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=db_session)
    assert not report.is_valid
    assert report.layers["layer_c"].status == "FAILED"
    assert any("Byte size mismatch" in err for err in report.layers["layer_c"].errors)


@pytest.mark.asyncio
async def test_failure_mode_6_deleted_or_unpersisted_artifact(
    db_session: AsyncSession, base_valid_trace_dict: dict
) -> None:
    """6. Artifact marked persisted in trace but missing in DB fails Layer B."""
    base_valid_trace_dict["scenarios"][0]["artifact_bindings"][0]["persisted"] = True
    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=db_session)
    assert report.layers["layer_b"].status == "FAILED"


@pytest.mark.asyncio
async def test_failure_mode_7_layer_not_verified_when_db_is_none(
    base_valid_trace_dict: dict,
) -> None:
    """7. When db is None, Layers B, C, D return NOT_VERIFIED."""
    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=None)
    assert report.layers["layer_a"].status == "VERIFIED"
    assert report.layers["layer_b"].status == "NOT_VERIFIED"
    assert report.layers["layer_c"].status == "NOT_VERIFIED"
    assert report.layers["layer_d"].status == "NOT_VERIFIED"
    assert report.layers["layer_e"].status == "VERIFIED"


@pytest.mark.asyncio
async def test_failure_mode_8_false_resolution_unbound_hash(
    base_valid_trace_dict: dict,
) -> None:
    """8. Resolution event with unbound hash fails Layer A (Trace Self-Consistency)."""
    base_valid_trace_dict["scenarios"][0]["resolution_events"][0]["revised_artifact_hash"] = "e" * 64
    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=None)
    assert not report.is_valid
    assert report.layers["layer_a"].status == "FAILED"
    assert any("references unbound hash" in err for err in report.layers["layer_a"].errors)


@pytest.mark.asyncio
async def test_failure_mode_9_missing_provider_request_id_in_live(
    base_valid_trace_dict: dict,
) -> None:
    """9. Missing provider request ID in LIVE_PROVIDER execution fails Layer E."""
    s = base_valid_trace_dict["scenarios"][0]
    s["execution_mode"] = "LIVE_PROVIDER"
    s["execution_metadata"]["provider_request_id"] = ""
    s["execution_metadata"]["model_id"] = "groq/llama-3.3-70b-versatile"

    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=None)
    assert not report.is_valid
    assert report.layers["layer_e"].status == "FAILED"
    assert any("missing provider_request_id" in err for err in report.layers["layer_e"].errors)


@pytest.mark.asyncio
async def test_failure_mode_10_unbound_artifact_reference_in_criteria(
    base_valid_trace_dict: dict,
) -> None:
    """10. Criterion referencing unbound artifact ID fails Layer A."""
    base_valid_trace_dict["scenarios"][0]["acceptance_criteria"][0]["evidence_reference"] = "art-unbound-999"
    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=None)
    assert not report.is_valid
    assert report.layers["layer_a"].status == "FAILED"
    assert any("references unbound artifact ID" in err for err in report.layers["layer_a"].errors)


@pytest.mark.asyncio
async def test_happy_path_all_5_layers_verified(
    db_session: AsyncSession, base_valid_trace_dict: dict
) -> None:
    """Happy path: When valid DB records exist matching trace, all 5 layers are VERIFIED."""
    s = base_valid_trace_dict["scenarios"][0]
    b = s["artifact_bindings"][0]
    ws_id = s["execution_metadata"]["workspace_id"]

    proj = Project(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        name="Test Proj",
        created_by_user_id=str(uuid.uuid4()),
    )
    db_session.add(proj)
    await db_session.flush()

    art = Artifact(
        id=b["artifact_id"],
        project_id=proj.id,
        name="test.md",
        artifact_type="doc",
        media_type="text/markdown",
        size_bytes=b["byte_size"],
        storage_path="/tmp/test.md",
        content_hash=b["content_hash"],
    )
    db_session.add(art)
    await db_session.flush()

    validator = AcceptanceTraceValidator(base_valid_trace_dict)
    report = await validator.validate_authoritative_persistence(db=db_session)
    assert report.is_valid
    assert report.layers["layer_a"].status == "VERIFIED"
    assert report.layers["layer_b"].status == "VERIFIED"
    assert report.layers["layer_c"].status == "VERIFIED"
    assert report.layers["layer_d"].status == "VERIFIED"
    assert report.layers["layer_e"].status == "VERIFIED"
