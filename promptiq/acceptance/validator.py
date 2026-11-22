"""Independent Acceptance Trace Validator for PromptIQ.

Performs standalone, rigorous verification of acceptance traces against persisted
database records, cryptographic hashes, step chronologies, finding lifecycles,
and provenance rules. Completely decoupled from the trace generation pipeline.
"""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.models.memory import Artifact
from promptiq.models.package import PromptPackage
from promptiq.models.project import Project
from promptiq.models.research import EvidenceClaim, ResearchJob, SourceRecord


class ValidationErrorDetail(BaseModel):
    """Detailed error record for a failed validation check."""

    check_name: str
    scenario_id: str | None = None
    entity_id: str | None = None
    message: str
    severity: str = "critical"  # critical, high, medium, low

    model_config = ConfigDict(from_attributes=True)


class LayerResult(BaseModel):
    """Result of an individual verification layer."""

    layer: str  # "Layer A", "Layer B", "Layer C", "Layer D", "Layer E"
    name: str
    status: str  # "VERIFIED", "FAILED", "NOT_VERIFIED"
    details: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AuthoritativePersistenceReport(BaseModel):
    """Result of multi-layered authoritative persistence verification."""

    is_valid: bool
    layers: dict[str, LayerResult]
    total_artifacts_checked: int
    verified_artifacts: int
    failed_artifacts: int
    unverified_artifacts: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class ValidationReport(BaseModel):
    """Comprehensive outcome of independent acceptance trace validation."""

    is_valid: bool
    total_checks_evaluated: int
    passed_checks: int
    failed_checks: int
    errors: list[ValidationErrorDetail] = Field(default_factory=list)
    scenario_verdicts: dict[str, str] = Field(default_factory=dict)
    validated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class TraceValidationError(Exception):
    """Raised when trace data violates structural or integrity constraints."""


class AcceptanceTraceValidator:
    """Independent validator verifying acceptance traces without self-attestation."""

    VALID_TRANSITIONS: dict[str, set[str]] = {
        "STEP_EXECUTED": {
            "STEP_VALIDATED",
            "REVIEW_REQUIRED",
            "NEEDS_REVISION",
            "BLOCKED",
            "FAILED",
        },
        "STEP_VALIDATED": {
            "STEP_EXECUTED",
            "REVIEW_REQUIRED",
            "NEEDS_REVISION",
            "REVISION_IN_PROGRESS",
            "COMPLETED_WITH_WARNINGS",
            "SUCCESS_FULLY_VERIFIED",
            "BLOCKED",
            "FAILED",
        },
        "REVIEW_REQUIRED": {
            "STEP_VALIDATED",
            "NEEDS_REVISION",
            "REVISION_IN_PROGRESS",
            "COMPLETED_WITH_WARNINGS",
            "BLOCKED",
            "FAILED",
        },
        "NEEDS_REVISION": {
            "REVISION_IN_PROGRESS",
            "BLOCKED",
            "FAILED",
        },
        "REVISION_IN_PROGRESS": {
            "REVISION_VERIFIED",
            "NEEDS_REVISION",
            "BLOCKED",
            "FAILED",
        },
        "REVISION_VERIFIED": {
            "STEP_VALIDATED",
            "STEP_EXECUTED",
            "REVIEW_REQUIRED",
            "NEEDS_REVISION",
            "COMPLETED_WITH_WARNINGS",
            "SUCCESS_FULLY_VERIFIED",
            "BLOCKED",
            "FAILED",
        },
        "COMPLETED_WITH_WARNINGS": set(),
        "SUCCESS_FULLY_VERIFIED": set(),
        "BLOCKED": set(),
        "FAILED": set(),
    }

    def __init__(self, trace_source: str | Path | dict[str, Any]):
        if isinstance(trace_source, (str, Path)):
            with open(trace_source, encoding="utf-8") as f:
                self.trace_data = json.load(f)
        elif isinstance(trace_source, dict):
            self.trace_data = trace_source
        else:
            raise ValueError(f"Unsupported trace source type: {type(trace_source)}")

        self.errors: list[ValidationErrorDetail] = []
        self.checks_count: int = 0

    def _record_error(
        self,
        check_name: str,
        message: str,
        scenario_id: str | None = None,
        entity_id: str | None = None,
        severity: str = "critical",
    ) -> None:
        self.errors.append(
            ValidationErrorDetail(
                check_name=check_name,
                scenario_id=scenario_id,
                entity_id=entity_id,
                message=message,
                severity=severity,
            )
        )

    def validate_structure_and_ids(self) -> None:
        """Validates top-level trace structure, runner version, and scenario ID uniqueness."""
        self.checks_count += 1
        if not isinstance(self.trace_data, dict):
            self._record_error("structure", "Trace root must be a JSON object")
            return

        scenarios = self.trace_data.get("scenarios")
        if not isinstance(scenarios, list) or len(scenarios) == 0:
            self._record_error("structure", "Trace must contain a non-empty 'scenarios' list")
            return

        seen_ids = set()
        for s in scenarios:
            sid = s.get("scenario_id")
            if not sid or not isinstance(sid, str):
                self._record_error("scenario_id", "Scenario missing valid non-empty 'scenario_id'")
                continue
            if sid in seen_ids:
                self._record_error(
                    "duplicate_id", f"Duplicate scenario ID found: '{sid}'", scenario_id=sid
                )
            seen_ids.add(sid)

    def validate_state_transitions(self, scenario: dict[str, Any]) -> None:
        """Validates that every state transition in the scenario is legal and consistent."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        transitions = scenario.get("transitions", [])
        if not transitions:
            self._record_error(
                "transitions", "Scenario contains zero recorded transitions", scenario_id=sid
            )
            return

        for t in transitions:
            from_s = t.get("from_state")
            to_s = t.get("to_state")
            if not from_s or not to_s:
                self._record_error(
                    "transition_states",
                    "Transition missing from_state or to_state",
                    scenario_id=sid,
                )
                continue

            # Idempotent re-evaluation
            if from_s == to_s and from_s in ("STEP_VALIDATED", "STEP_EXECUTED", "REVIEW_REQUIRED"):
                continue

            allowed = self.VALID_TRANSITIONS.get(from_s, set())
            if to_s not in allowed:
                self._record_error(
                    "illegal_transition",
                    f"Illegal state transition from '{from_s}' to '{to_s}'",
                    scenario_id=sid,
                    entity_id=t.get("transition_id"),
                )

        # Terminal state agreement
        term_state = scenario.get("terminal_state")
        curr_state = scenario.get("current_state")
        if curr_state != term_state:
            self._record_error(
                "terminal_state_mismatch",
                f"current_state '{curr_state}' does not match terminal_state '{term_state}'",
                scenario_id=sid,
            )

    def validate_step_timings(self, scenario: dict[str, Any]) -> None:
        """Validates that all steps have monotonic timestamps and completed_at >= started_at."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        steps = scenario.get("steps", [])

        for step in steps:
            s_name = step.get("step_name", "UNKNOWN")
            s_time_raw = step.get("started_at")
            c_time_raw = step.get("completed_at")
            dur = step.get("duration_ms")

            if not s_time_raw or not c_time_raw:
                self._record_error(
                    "missing_timestamp",
                    f"Step '{s_name}' is missing started_at or completed_at timestamp",
                    scenario_id=sid,
                    entity_id=s_name,
                )
                continue

            try:
                s_dt = datetime.fromisoformat(s_time_raw.replace("Z", "+00:00"))
                c_dt = datetime.fromisoformat(c_time_raw.replace("Z", "+00:00"))
            except Exception as e:
                self._record_error(
                    "invalid_timestamp_format",
                    f"Step '{s_name}' has unparseable ISO timestamp: {e}",
                    scenario_id=sid,
                    entity_id=s_name,
                )
                continue

            if c_dt < s_dt:
                self._record_error(
                    "impossible_timestamp_order",
                    f"Step '{s_name}' completed_at ({c_time_raw}) precedes started_at ({s_time_raw})",
                    scenario_id=sid,
                    entity_id=s_name,
                )

            if dur is not None and dur < 0:
                self._record_error(
                    "negative_duration",
                    f"Step '{s_name}' has negative duration_ms ({dur})",
                    scenario_id=sid,
                    entity_id=s_name,
                )

    def validate_acceptance_criteria(self, scenario: dict[str, Any]) -> None:
        """Validates that all mandatory criteria are satisfied with verifiable, resolvable references."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        criteria = scenario.get("acceptance_criteria", [])
        term_state = scenario.get("terminal_state")

        # Collect bound artifacts and hashes for reference resolution
        bindings = scenario.get("artifact_bindings", [])
        bound_ids = {b.get("artifact_id") for b in bindings if b.get("artifact_id")}
        bound_hashes = {b.get("content_hash") for b in bindings if b.get("content_hash")}

        for c in criteria:
            cid = c.get("id", "UNKNOWN")
            is_mand = c.get("is_mandatory", True)
            satisfied = c.get("satisfied", False)
            evidence = c.get("evidence")
            ref = c.get("evidence_reference")
            data = c.get("verifiable_data")
            rtype = c.get("evidence_record_type")

            # In terminal success or completed_with_warnings, mandatory criteria must be satisfied
            if (
                term_state in ("SUCCESS_FULLY_VERIFIED", "COMPLETED_WITH_WARNINGS")
                and is_mand
                and not satisfied
            ):
                self._record_error(
                    "unsatisfied_mandatory_criterion",
                    f"Mandatory criterion '{cid}' is unsatisfied in terminal state '{term_state}'",
                    scenario_id=sid,
                    entity_id=cid,
                )

            if satisfied:
                if not evidence or not evidence.strip():
                    self._record_error(
                        "empty_criterion_evidence",
                        f"Satisfied criterion '{cid}' has blank evidence",
                        scenario_id=sid,
                        entity_id=cid,
                    )
                # Check for verifiable reference (token or field)
                has_ref_token = any(
                    tok in str(evidence)
                    for tok in [
                        "SHA-256",
                        "hash:",
                        "ID:",
                        "id:",
                        "0x",
                        "test_",
                        "artifact",
                        "SC",
                        "pkg-",
                        "PRD-",
                        "TASK-",
                        "rubric",
                        "score",
                    ]
                )
                if is_mand and not (ref or data or has_ref_token):
                    self._record_error(
                        "unsupported_prose_evidence",
                        f"Mandatory criterion '{cid}' satisfied with prose lacking verifiable reference: '{evidence}'",
                        scenario_id=sid,
                        entity_id=cid,
                    )

                # Grounding & Resolution verification:
                # 1. Any 64-character SHA-256 hash mentioned in evidence or ref MUST resolve to actual scenario artifact bindings
                ev_str = f"{evidence} {ref or ''}"
                claimed_hashes = re.findall(r"\b[0-9a-fA-F]{64}\b", ev_str)
                for h in claimed_hashes:
                    if h not in bound_hashes:
                        self._record_error(
                            "unresolved_evidence_reference",
                            f"Mandatory criterion '{cid}' references artifact hash '{h}' which is not in scenario artifact_bindings",
                            scenario_id=sid,
                            entity_id=cid,
                        )

                # 2. If evidence_record_type is 'artifact', the reference MUST exist in scenario artifact bindings
                if rtype == "artifact" and ref:
                    if ref not in bound_ids:
                        self._record_error(
                            "unresolved_evidence_reference",
                            f"Mandatory criterion '{cid}' claims artifact reference '{ref}' which is not in scenario artifact_bindings",
                            scenario_id=sid,
                            entity_id=cid,
                        )

                # 3. If verifiable_data specifies an artifact_id or hash, it must resolve
                if isinstance(data, dict):
                    v_art_id = data.get("artifact_id")
                    if v_art_id and v_art_id not in bound_ids:
                        self._record_error(
                            "unresolved_evidence_reference",
                            f"Mandatory criterion '{cid}' verifiable_data artifact_id '{v_art_id}' is not in scenario artifact_bindings",
                            scenario_id=sid,
                            entity_id=cid,
                        )
                    v_hash = data.get("content_hash")
                    if v_hash and v_hash not in bound_hashes:
                        self._record_error(
                            "unresolved_evidence_reference",
                            f"Mandatory criterion '{cid}' verifiable_data content_hash '{v_hash}' is not in scenario artifact_bindings",
                            scenario_id=sid,
                            entity_id=cid,
                        )

    def validate_autopsy_and_resolution_lifecycle(self, scenario: dict[str, Any]) -> None:
        """Validates lifecycle consistency: immutable initial autopsy, current ledger, and resolution events."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")

        initial_aut = scenario.get("initial_autopsy")
        aut_findings = scenario.get("autopsy_findings", [])
        unres_findings = scenario.get("unresolved_findings", [])
        res_events = scenario.get("resolution_events", [])

        # Map resolution events
        resolved_finding_ids = {
            r.get("finding_id") for r in res_events if r.get("status") == "resolved"
        }

        # Check resolution event integrity
        for rev in res_events:
            rid = rev.get("resolution_id", "UNKNOWN")
            fid = rev.get("finding_id")
            rev_hash = rev.get("revised_artifact_hash")
            if not fid:
                self._record_error(
                    "orphan_resolution_event",
                    f"Resolution event '{rid}' lacks finding_id",
                    scenario_id=sid,
                    entity_id=rid,
                )
            if not rev_hash or len(rev_hash) < 16:
                self._record_error(
                    "invalid_resolution_hash",
                    f"Resolution event '{rid}' lacks valid revised_artifact_hash",
                    scenario_id=sid,
                    entity_id=rid,
                )

        # In the active findings ledger (autopsy_findings):
        for f in aut_findings:
            fid = f.get("id")
            is_resolved = f.get("is_resolved", False)
            disposition = f.get("disposition")

            if fid in resolved_finding_ids:
                if not is_resolved or disposition != "resolved":
                    self._record_error(
                        "finding_ledger_inconsistency",
                        f"Finding '{fid}' was resolved in resolution_events but autopsy_findings shows is_resolved={is_resolved}, disposition='{disposition}'",
                        scenario_id=sid,
                        entity_id=fid,
                    )

        # Check that unresolved findings do not contain resolved IDs
        for uf in unres_findings:
            ufid = uf.get("id")
            if ufid in resolved_finding_ids:
                self._record_error(
                    "resolved_finding_in_unresolved_list",
                    f"Resolved finding '{ufid}' still present in unresolved_findings projection",
                    scenario_id=sid,
                    entity_id=ufid,
                )

        # Check that initial autopsy findings preserve historical integrity
        if initial_aut:
            init_findings = initial_aut.get("findings", [])
            for init_f in init_findings:
                # Historical snapshot must retain original pending disposition
                if init_f.get("is_resolved", False):
                    self._record_error(
                        "historical_autopsy_mutation",
                        f"Initial autopsy snapshot for '{init_f.get('id')}' was mutated to is_resolved=True",
                        scenario_id=sid,
                        entity_id=init_f.get("id"),
                    )

    def validate_warning_consistency(self, scenario: dict[str, Any]) -> None:
        """Validates bidirectional consistency between warnings strings and warning_records."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        warnings = scenario.get("warnings", [])
        warning_records = scenario.get("warning_records", [])
        term_state = scenario.get("terminal_state")
        unres = scenario.get("unresolved_findings", [])

        if term_state == "SUCCESS_FULLY_VERIFIED":
            if warnings:
                self._record_error(
                    "warnings_in_fully_verified",
                    f"SUCCESS_FULLY_VERIFIED has {len(warnings)} warnings",
                    scenario_id=sid,
                )
            if warning_records:
                self._record_error(
                    "warning_records_in_fully_verified",
                    f"SUCCESS_FULLY_VERIFIED has {len(warning_records)} warning_records",
                    scenario_id=sid,
                )

        elif term_state == "COMPLETED_WITH_WARNINGS":
            if not warnings and not unres:
                self._record_error(
                    "completed_with_warnings_missing_warnings",
                    "COMPLETED_WITH_WARNINGS has empty warnings array",
                    scenario_id=sid,
                )
            if len(warnings) != len(warning_records):
                self._record_error(
                    "warning_count_mismatch",
                    f"Warning count mismatch: {len(warnings)} warning strings vs {len(warning_records)} warning records",
                    scenario_id=sid,
                )

    def validate_artifact_bindings(self, scenario: dict[str, Any]) -> None:
        """Validates artifact bindings, content hashes, and byte sizes."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        bindings = scenario.get("artifact_bindings", [])
        term_state = scenario.get("terminal_state")

        if term_state in ("SUCCESS_FULLY_VERIFIED", "COMPLETED_WITH_WARNINGS") and not bindings:
            self._record_error(
                "missing_artifacts",
                "Completed scenario has zero artifact bindings",
                scenario_id=sid,
            )
            return

        for b in bindings:
            aid = b.get("artifact_id", "UNKNOWN")
            chash = b.get("content_hash")
            bsize = b.get("byte_size", 0)
            persisted = b.get("persisted", False)
            retrievable = b.get("retrievable", False)

            if not chash or len(chash) != 64:
                self._record_error(
                    "invalid_artifact_hash",
                    f"Artifact '{aid}' has invalid SHA-256 hash '{chash}'",
                    scenario_id=sid,
                    entity_id=aid,
                )

            if bsize <= 0:
                self._record_error(
                    "invalid_artifact_byte_size",
                    f"Artifact '{aid}' has invalid byte size {bsize}",
                    scenario_id=sid,
                    entity_id=aid,
                )

            if term_state in ("SUCCESS_FULLY_VERIFIED", "COMPLETED_WITH_WARNINGS"):
                if not persisted or not retrievable:
                    self._record_error(
                        "artifact_not_retrievable",
                        f"Artifact '{aid}' is not marked persisted and retrievable",
                        scenario_id=sid,
                        entity_id=aid,
                    )

    def validate_execution_provenance(self, scenario: dict[str, Any]) -> None:
        """Validates that mock execution is never labeled live or LIVE_PROVIDER."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        evals = scenario.get("evaluation_records", [])

        for ev in evals:
            mid = ev.get("model_id", "")
            route = str(ev.get("provider_route", "")).lower()
            emode = str(ev.get("execution_mode", "")).upper()

            is_mock = mid in ("promptiq-mock-v1", "mock") or route in ("mock", "synthetic")
            if is_mock and emode in ("LIVE", "LIVE_PROVIDER"):
                self._record_error(
                    "mock_labeled_live",
                    f"Mock model '{mid}' on route '{route}' is illegally labeled '{emode}'",
                    scenario_id=sid,
                    entity_id=mid,
                )

    def validate_research_provenance(self, scenario: dict[str, Any]) -> None:
        """Validates that simulated/synthetic research is never classified as live search."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        meta = scenario.get("execution_metadata", {})
        research_claims = meta.get("research_claims", [])

        for claim in research_claims:
            src_type = str(claim.get("source_type", "")).lower()
            cls_mode = str(claim.get("retrieval_classification", "")).upper()
            if src_type in ("mock", "simulated", "synthetic") and cls_mode in (
                "LIVE_SEARCH",
                "LIVE_EXTERNAL",
            ):
                self._record_error(
                    "simulated_research_labeled_live",
                    f"Simulated research claim '{claim.get('id')}' is illegally classified as '{cls_mode}'",
                    scenario_id=sid,
                    entity_id=claim.get("id"),
                )

    def validate_replay_integrity(self, scenario: dict[str, Any]) -> None:
        """Validates that replayed or cached provider calls are not marked fresh live executions."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        evals = scenario.get("evaluation_records", [])

        for ev in evals:
            is_replayed = ev.get("is_replayed", False) or ev.get("cached", False)
            emode = str(ev.get("execution_mode", "")).upper()
            has_replay_provenance = ev.get("replay_provenance_id") or ev.get(
                "resumed_from_request_id"
            )
            if is_replayed and emode == "LIVE" and not has_replay_provenance:
                self._record_error(
                    "replayed_provider_call_labeled_fresh",
                    f"Replayed provider call in evaluation '{ev.get('id')}' lacks replay provenance header",
                    scenario_id=sid,
                    entity_id=ev.get("id"),
                )

    def validate_tenant_isolation(self, scenario: dict[str, Any]) -> None:
        """Validates tenant isolation and prevents cross-tenant artifact references."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        meta = scenario.get("execution_metadata", {})
        scenario_ws = meta.get("workspace_id")
        bindings = scenario.get("artifact_bindings", [])

        if scenario_ws:
            for b in bindings:
                b_ws = b.get("workspace_id")
                if b_ws and b_ws != scenario_ws:
                    self._record_error(
                        "cross_tenant_artifact_access",
                        f"Artifact '{b.get('artifact_id')}' belongs to workspace '{b_ws}' but accessed in '{scenario_ws}'",
                        scenario_id=sid,
                        entity_id=b.get("artifact_id"),
                    )

    def validate_autopsy_version_targeting(self, scenario: dict[str, Any]) -> None:
        """Validates that final autopsy inspects the revised deliverable hash, not the original unrevised hash."""
        self.checks_count += 1
        sid = scenario.get("scenario_id", "UNKNOWN")
        final_aut = scenario.get("final_autopsy")
        rev_events = scenario.get("revision_events", [])

        if final_aut and rev_events:
            final_target_hash = final_aut.get("artifact_hash")
            original_hash = rev_events[0].get("original_artifact_hash")
            if final_target_hash and original_hash and final_target_hash == original_hash:
                self._record_error(
                    "autopsy_wrong_artifact_version",
                    f"Final autopsy evaluated obsolete pre-revision artifact hash '{final_target_hash}' instead of revised deliverable",
                    scenario_id=sid,
                    entity_id=final_aut.get("id"),
                )

    def validate_all(self) -> ValidationReport:
        """Executes all independent validation suites across all scenarios."""
        self.errors = []
        self.checks_count = 0
        scenario_verdicts = {}

        self.validate_structure_and_ids()

        scenarios = (
            self.trace_data.get("scenarios", []) if isinstance(self.trace_data, dict) else []
        )
        for s in scenarios:
            sid = s.get("scenario_id", "UNKNOWN")
            err_count_before = len(self.errors)

            self.validate_state_transitions(s)
            self.validate_step_timings(s)
            self.validate_acceptance_criteria(s)
            self.validate_autopsy_and_resolution_lifecycle(s)
            self.validate_warning_consistency(s)
            self.validate_artifact_bindings(s)
            self.validate_execution_provenance(s)
            self.validate_research_provenance(s)
            self.validate_replay_integrity(s)
            self.validate_tenant_isolation(s)
            self.validate_autopsy_version_targeting(s)

            scenario_errs = len(self.errors) - err_count_before
            scenario_verdicts[sid] = "VALID" if scenario_errs == 0 else "INVALID"

        is_valid = len(self.errors) == 0
        failed_checks = len(self.errors)
        passed_checks = max(0, self.checks_count - failed_checks)

        return ValidationReport(
            is_valid=is_valid,
            total_checks_evaluated=self.checks_count,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            errors=self.errors,
            scenario_verdicts=scenario_verdicts,
        )

    async def validate_authoritative_persistence(
        self, db: AsyncSession | None = None
    ) -> AuthoritativePersistenceReport:
        """Executes multi-layered authoritative persistence verification across all 5 layers."""
        scenarios = (
            self.trace_data.get("scenarios", []) if isinstance(self.trace_data, dict) else []
        )

        # Layer A: Trace Self-Consistency
        layer_a_errors: list[str] = []
        all_bindings: list[dict[str, Any]] = []
        for s in scenarios:
            sid = s.get("scenario_id", "UNKNOWN")
            bindings = s.get("artifact_bindings", [])
            all_bindings.extend(bindings)
            bound_ids = {b.get("artifact_id") for b in bindings if b.get("artifact_id")}
            bound_hashes = {b.get("content_hash") for b in bindings if b.get("content_hash")}

            for b in bindings:
                aid = b.get("artifact_id")
                chash = b.get("content_hash")
                bsize = b.get("byte_size", 0)
                if not aid:
                    layer_a_errors.append(f"[{sid}] Binding missing artifact_id")
                if not chash or len(chash) != 64:
                    layer_a_errors.append(
                        f"[{sid}] Binding '{aid}' has invalid SHA-256 hash: {chash}"
                    )
                if bsize <= 0:
                    layer_a_errors.append(
                        f"[{sid}] Binding '{aid}' has non-positive byte_size: {bsize}"
                    )

            # Check criteria reference resolution
            for c in s.get("acceptance_criteria", []):
                ref = c.get("evidence_reference")
                rtype = c.get("evidence_record_type")
                if rtype == "artifact" and ref and ref not in bound_ids:
                    layer_a_errors.append(
                        f"[{sid}] Criterion '{c.get('id')}' references unbound artifact ID '{ref}'"
                    )

            # Check resolution events resolution
            for r in s.get("resolution_events", []):
                rev_hash = r.get("revised_artifact_hash")
                if rev_hash and rev_hash not in bound_hashes:
                    layer_a_errors.append(
                        f"[{sid}] Resolution event '{r.get('resolution_id')}' references unbound hash '{rev_hash}'"
                    )

        layer_a = LayerResult(
            layer="Layer A",
            name="Trace Self-Consistency",
            status="VERIFIED" if not layer_a_errors else "FAILED",
            details={"artifacts_in_trace": len(all_bindings)},
            errors=layer_a_errors,
        )

        # Layer B: Database Record Verification
        layer_b_errors: list[str] = []
        db_records: dict[str, Any] = {}
        if db is None:
            layer_b = LayerResult(
                layer="Layer B",
                name="Database Record Verification",
                status="NOT_VERIFIED",
                details={"reason": "No database session provided"},
                errors=[],
            )
        else:
            for s in scenarios:
                sid = s.get("scenario_id", "UNKNOWN")
                for b in s.get("artifact_bindings", []):
                    aid = b.get("artifact_id")
                    if not aid:
                        continue
                    # Query Artifact
                    art_stmt = select(Artifact).where(Artifact.id == aid)
                    art_res = await db.execute(art_stmt)
                    art = art_res.scalar_one_or_none()
                    if art:
                        db_records[aid] = ("Artifact", art, art.project_id)
                    else:
                        pkg_stmt = select(PromptPackage).where(PromptPackage.id == aid)
                        pkg_res = await db.execute(pkg_stmt)
                        pkg = pkg_res.scalar_one_or_none()
                        if pkg:
                            db_records[aid] = ("PromptPackage", pkg, pkg.project_id)
                        else:
                            src_stmt = select(SourceRecord).where(SourceRecord.id == aid)
                            src_res = await db.execute(src_stmt)
                            src = src_res.scalar_one_or_none()
                            if src:
                                job_stmt = select(ResearchJob).where(
                                    ResearchJob.id == src.research_job_id
                                )
                                job_res = await db.execute(job_stmt)
                                job = job_res.scalar_one_or_none()
                                db_records[aid] = (
                                    "SourceRecord",
                                    src,
                                    job.project_id if job else None,
                                )
                            else:
                                claim_stmt = select(EvidenceClaim).where(EvidenceClaim.id == aid)
                                claim_res = await db.execute(claim_stmt)
                                claim = claim_res.scalar_one_or_none()
                                if claim:
                                    job_stmt = select(ResearchJob).where(
                                        ResearchJob.id == claim.research_job_id
                                    )
                                    job_res = await db.execute(job_stmt)
                                    job = job_res.scalar_one_or_none()
                                    db_records[aid] = (
                                        "EvidenceClaim",
                                        claim,
                                        job.project_id if job else None,
                                    )
                                elif b.get("persisted", False):
                                    layer_b_errors.append(
                                        f"[{sid}] Persisted artifact '{aid}' does not exist in database"
                                    )

            layer_b = LayerResult(
                layer="Layer B",
                name="Database Record Verification",
                status="VERIFIED" if not layer_b_errors else "FAILED",
                details={"records_found": len(db_records)},
                errors=layer_b_errors,
            )

        # Layer C: Artifact Byte Integrity
        layer_c_errors: list[str] = []
        if db is None:
            layer_c = LayerResult(
                layer="Layer C",
                name="Artifact Byte Integrity",
                status="NOT_VERIFIED",
                details={"reason": "No database session provided"},
                errors=[],
            )
        else:
            for s in scenarios:
                sid = s.get("scenario_id", "UNKNOWN")
                for b in s.get("artifact_bindings", []):
                    aid = b.get("artifact_id")
                    if aid not in db_records:
                        continue
                    rec_type, rec, _ = db_records[aid]
                    expected_hash = b.get("content_hash")
                    expected_size = b.get("byte_size")

                    if rec_type == "Artifact":
                        if rec.content_hash != expected_hash:
                            layer_c_errors.append(
                                f"[{sid}] Byte hash mismatch for Artifact '{aid}': expected {expected_hash}, DB has {rec.content_hash}"
                            )
                        if expected_size and rec.size_bytes != expected_size:
                            layer_c_errors.append(
                                f"[{sid}] Byte size mismatch for Artifact '{aid}': expected {expected_size}, DB has {rec.size_bytes}"
                            )
                    elif rec_type == "PromptPackage":
                        # Check manifest, joined files text, or serialized JSON files
                        raw_files = json.dumps(rec.files, sort_keys=True).encode("utf-8")
                        calc_hash = hashlib.sha256(raw_files).hexdigest()
                        raw_text = (
                            "\n\n".join(rec.files.values()).encode("utf-8") if rec.files else b""
                        )
                        calc_text_hash = hashlib.sha256(raw_text).hexdigest() if raw_text else ""
                        pkg_hash = rec.manifest.get("package_hash") or calc_hash
                        valid_hashes = {h for h in (pkg_hash, calc_hash, calc_text_hash) if h}
                        if expected_hash and expected_hash not in valid_hashes:
                            layer_c_errors.append(
                                f"[{sid}] Byte hash mismatch for PromptPackage '{aid}': expected {expected_hash}, calculated {calc_text_hash or calc_hash}"
                            )
                    elif rec_type == "SourceRecord":
                        raw_title = (rec.title or rec.url).encode("utf-8")
                        calc_hash = hashlib.sha256(raw_title).hexdigest()
                        raw_url = rec.url.encode("utf-8")
                        calc_url_hash = hashlib.sha256(raw_url).hexdigest()
                        if expected_hash and expected_hash not in (calc_hash, calc_url_hash):
                            layer_c_errors.append(
                                f"[{sid}] Byte hash mismatch for SourceRecord '{aid}': expected {expected_hash}, calculated {calc_hash}"
                            )
                    elif rec_type == "EvidenceClaim":
                        raw_claim = rec.claim_text.encode("utf-8")
                        calc_hash = hashlib.sha256(raw_claim).hexdigest()
                        if expected_hash and expected_hash != calc_hash:
                            layer_c_errors.append(
                                f"[{sid}] Byte hash mismatch for EvidenceClaim '{aid}': expected {expected_hash}, calculated {calc_hash}"
                            )

            layer_c = LayerResult(
                layer="Layer C",
                name="Artifact Byte Integrity",
                status="VERIFIED" if not layer_c_errors else "FAILED",
                details={"verified_count": len(db_records) - len(layer_c_errors)},
                errors=layer_c_errors,
            )

        # Layer D: Tenant Ownership Verification
        layer_d_errors: list[str] = []
        if db is None:
            layer_d = LayerResult(
                layer="Layer D",
                name="Tenant Ownership Verification",
                status="NOT_VERIFIED",
                details={"reason": "No database session provided"},
                errors=[],
            )
        else:
            for s in scenarios:
                sid = s.get("scenario_id", "UNKNOWN")
                meta = s.get("execution_metadata", {})
                scenario_ws = meta.get("workspace_id")
                for b in s.get("artifact_bindings", []):
                    aid = b.get("artifact_id")
                    if aid not in db_records:
                        continue
                    rec_type, rec, proj_id = db_records[aid]
                    if not proj_id:
                        continue
                    # Query project
                    proj_stmt = select(Project).where(Project.id == proj_id)
                    p_res = await db.execute(proj_stmt)
                    proj = p_res.scalar_one_or_none()
                    if not proj:
                        layer_d_errors.append(
                            f"[{sid}] Project '{proj_id}' for artifact '{aid}' not found"
                        )
                    elif scenario_ws and proj.workspace_id != scenario_ws:
                        layer_d_errors.append(
                            f"[{sid}] Cross-tenant violation: Artifact '{aid}' owned by workspace '{proj.workspace_id}', accessed in '{scenario_ws}'"
                        )

            layer_d = LayerResult(
                layer="Layer D",
                name="Tenant Ownership Verification",
                status="VERIFIED" if not layer_d_errors else "FAILED",
                details={"tenants_checked": len(scenarios)},
                errors=layer_d_errors,
            )

        # Layer E: External Execution Provenance
        layer_e_errors: list[str] = []
        for s in scenarios:
            sid = s.get("scenario_id", "UNKNOWN")
            mode = s.get("execution_mode")
            meta = s.get("execution_metadata", {})
            prov_req_id = meta.get("provider_request_id")
            model_id = meta.get("model_id")

            if mode == "LIVE_PROVIDER":
                if not prov_req_id or not prov_req_id.strip():
                    layer_e_errors.append(
                        f"[{sid}] LIVE_PROVIDER execution missing provider_request_id"
                    )
                if not model_id or not model_id.strip():
                    layer_e_errors.append(f"[{sid}] LIVE_PROVIDER execution missing model_id")
            elif mode in ("MOCK", "SYNTHETIC"):
                if prov_req_id and "live" in prov_req_id.lower():
                    layer_e_errors.append(
                        f"[{sid}] Mock execution falsely claims live provider_request_id '{prov_req_id}'"
                    )

        layer_e = LayerResult(
            layer="Layer E",
            name="External Execution Provenance",
            status="VERIFIED" if not layer_e_errors else "FAILED",
            details={"scenarios_provenance_checked": len(scenarios)},
            errors=layer_e_errors,
        )

        layers = {
            "layer_a": layer_a,
            "layer_b": layer_b,
            "layer_c": layer_c,
            "layer_d": layer_d,
            "layer_e": layer_e,
        }

        has_failed = any(layer.status == "FAILED" for layer in layers.values())
        is_valid = not has_failed

        tot_checked = len(all_bindings)
        ver_count = len(db_records) - len(layer_c_errors) if db else 0
        unver_count = tot_checked if db is None else 0
        failed_count = (
            len(layer_a_errors)
            + len(layer_b_errors)
            + len(layer_c_errors)
            + len(layer_d_errors)
            + len(layer_e_errors)
        )

        return AuthoritativePersistenceReport(
            is_valid=is_valid,
            layers=layers,
            total_artifacts_checked=tot_checked,
            verified_artifacts=ver_count,
            failed_artifacts=failed_count,
            unverified_artifacts=unver_count,
        )
