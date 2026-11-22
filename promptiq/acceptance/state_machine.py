"""Acceptance State Machine and Quality Gate Enforcement for PromptIQ.

Implements the formal state machine, valid transition matrix, gate checks,
and cryptographic artifact verification.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

from promptiq.schemas.acceptance import (
    AcceptanceCriterion,
    ArtifactBinding,
    AutopsyInspectionRecord,
    ExecutionMode,
    ExecutionState,
    FindingResolutionEvent,
    RevisionEventRecord,
    ScenarioAuditTrace,
    StateTransitionRecord,
    StepRecord,
    WarningRecord,
)


class AcceptanceError(Exception):
    """Base exception for acceptance state machine errors."""


class InvalidTransitionError(AcceptanceError):
    """Raised when an illegal state transition is attempted."""


class GateValidationError(AcceptanceError):
    """Raised when quality gate conditions are violated."""


class ArtifactBindingError(AcceptanceError):
    """Raised when an inspected artifact does not match its registered cryptographic binding."""


class AcceptanceStateMachine:
    """Rigorous state machine tracking acceptance scenario lifecycle with gate validation."""

    # Explicit directed transition matrix
    VALID_TRANSITIONS: dict[ExecutionState, set[ExecutionState]] = {
        ExecutionState.STEP_EXECUTED: {
            ExecutionState.STEP_VALIDATED,
            ExecutionState.REVIEW_REQUIRED,
            ExecutionState.NEEDS_REVISION,
            ExecutionState.BLOCKED,
            ExecutionState.FAILED,
        },
        ExecutionState.STEP_VALIDATED: {
            ExecutionState.STEP_EXECUTED,  # next step
            ExecutionState.REVIEW_REQUIRED,
            ExecutionState.NEEDS_REVISION,
            ExecutionState.REVISION_IN_PROGRESS,
            ExecutionState.COMPLETED_WITH_WARNINGS,
            ExecutionState.SUCCESS_FULLY_VERIFIED,
            ExecutionState.BLOCKED,
            ExecutionState.FAILED,
        },
        ExecutionState.REVIEW_REQUIRED: {
            ExecutionState.STEP_VALIDATED,
            ExecutionState.NEEDS_REVISION,
            ExecutionState.REVISION_IN_PROGRESS,
            ExecutionState.COMPLETED_WITH_WARNINGS,
            ExecutionState.BLOCKED,
            ExecutionState.FAILED,
        },
        ExecutionState.NEEDS_REVISION: {
            ExecutionState.REVISION_IN_PROGRESS,
            ExecutionState.BLOCKED,
            ExecutionState.FAILED,
        },
        ExecutionState.REVISION_IN_PROGRESS: {
            ExecutionState.REVISION_VERIFIED,
            ExecutionState.NEEDS_REVISION,
            ExecutionState.BLOCKED,
            ExecutionState.FAILED,
        },
        ExecutionState.REVISION_VERIFIED: {
            ExecutionState.STEP_VALIDATED,
            ExecutionState.REVIEW_REQUIRED,
            ExecutionState.NEEDS_REVISION,
            ExecutionState.COMPLETED_WITH_WARNINGS,
            ExecutionState.SUCCESS_FULLY_VERIFIED,
            ExecutionState.BLOCKED,
            ExecutionState.FAILED,
        },
        # Terminal states have no valid transitions out
        ExecutionState.COMPLETED_WITH_WARNINGS: set(),
        ExecutionState.BLOCKED: set(),
        ExecutionState.FAILED: set(),
        ExecutionState.SUCCESS_FULLY_VERIFIED: set(),
    }

    def __init__(
        self,
        scenario_id: str,
        category: str,
        input_summary: dict[str, Any],
        execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC,
        initial_state: ExecutionState = ExecutionState.STEP_EXECUTED,
    ) -> None:
        self.scenario_id = scenario_id
        self.category = category
        self.input_summary = input_summary
        self.execution_mode = execution_mode
        self.current_state = initial_state
        self.terminal_state: ExecutionState | None = None

        self.steps: list[StepRecord] = []
        self.transitions: list[StateTransitionRecord] = []
        self.acceptance_criteria: list[AcceptanceCriterion] = []
        self.artifact_bindings: dict[str, ArtifactBinding] = {}
        self.initial_autopsy: AutopsyInspectionRecord | None = None
        self.revision_events: list[RevisionEventRecord] = []
        self.resolution_events: list[FindingResolutionEvent] = []
        self.final_autopsy: AutopsyInspectionRecord | None = None
        self.autopsy_findings: list[dict[str, Any]] = []
        self.unresolved_findings: list[dict[str, Any]] = []
        self.evaluation_records: list[dict[str, Any]] = []
        self.warning_records: list[WarningRecord] = []
        self.warnings: list[str] = []
        self.blocking_reasons: list[str] = []
        self.metadata: dict[str, Any] = {}

    def record_autopsy_run(
        self,
        phase: str,
        artifact_id: str,
        artifact_hash: str,
        verdict: str,
        findings: list[dict[str, Any]],
        quality_scores: dict[str, float] | None = None,
    ) -> AutopsyInspectionRecord:
        """Records an immutable Autopsy diagnosis event."""
        rec = AutopsyInspectionRecord(
            phase=phase,
            artifact_id=artifact_id,
            artifact_hash=artifact_hash,
            verdict=verdict,
            findings_count=len(findings),
            findings=findings,
            quality_scores=quality_scores or {},
        )
        if phase == "initial":
            self.initial_autopsy = rec
            self.autopsy_findings = list(findings)
            self.unresolved_findings = list(findings)
        elif phase == "final":
            self.final_autopsy = rec
        return rec

    def record_revision_event(
        self,
        previous_artifact_id: str,
        previous_artifact_hash: str,
        revised_artifact_id: str,
        revised_artifact_hash: str,
        changes_summary: str = "",
    ) -> RevisionEventRecord:
        """Records an immutable artifact revision event."""
        rev = RevisionEventRecord(
            previous_artifact_id=previous_artifact_id,
            previous_artifact_hash=previous_artifact_hash,
            revised_artifact_id=revised_artifact_id,
            revised_artifact_hash=revised_artifact_hash,
            changes_summary=changes_summary,
        )
        self.revision_events.append(rev)
        return rev

    def record_finding_resolution(
        self,
        finding_id: str,
        original_category: str,
        original_severity: str,
        revised_artifact_hash: str,
        status: str,
        resolution_evidence: str,
        verification_reason: str,
    ) -> FindingResolutionEvent:
        """Records a finding resolution event bound to the revised artifact hash."""
        res = FindingResolutionEvent(
            finding_id=finding_id,
            original_category=original_category,
            original_severity=original_severity,
            revised_artifact_hash=revised_artifact_hash,
            status=status,
            resolution_evidence=resolution_evidence,
            verification_reason=verification_reason,
        )
        self.resolution_events.append(res)
        return res

    def derive_unresolved_findings_and_warnings(self) -> list[dict[str, Any]]:
        """Derives current unresolved findings and populates warning records from findings."""
        resolved_ids = {
            r.finding_id for r in self.resolution_events if r.status == "resolved"
        }
        source_findings = self.autopsy_findings if self.autopsy_findings else self.unresolved_findings
        unresolved: list[dict[str, Any]] = []
        for f in source_findings:
            fid = f.get("id")
            if fid and fid not in resolved_ids:
                unresolved.append(f)

        # Also include any new findings from final autopsy
        if self.final_autopsy:
            existing_fids = {f.get("id") for f in unresolved}
            for ff in self.final_autopsy.findings:
                if ff.get("id") not in existing_fids:
                    unresolved.append(ff)

        self.unresolved_findings = unresolved

        # Populate structured warning records and text warnings
        self.warning_records = []
        for uf in unresolved:
            warn = WarningRecord(
                finding_id=uf.get("id", "UNKNOWN"),
                severity=uf.get("severity", "medium"),
                category=uf.get("category", "general"),
                finding_text=uf.get("finding", ""),
                consequence=uf.get("consequence", ""),
                recommendation=uf.get("recommendation", ""),
            )
            self.warning_records.append(warn)
            warn_str = (
                f"[{warn.finding_id}] ({warn.severity}) {warn.category}: {warn.finding_text} - "
                f"Consequence: {warn.consequence} - Recommendation: {warn.recommendation}"
            )
            if warn_str not in self.warnings:
                self.warnings.append(warn_str)

        return self.unresolved_findings

    def add_criterion(self, criterion_id: str, description: str, is_mandatory: bool = True) -> None:
        """Registers a required acceptance condition."""
        self.acceptance_criteria.append(
            AcceptanceCriterion(
                id=criterion_id,
                description=description,
                is_mandatory=is_mandatory,
                satisfied=False,
            )
        )

    def mark_criterion_satisfied(self, criterion_id: str, evidence: str) -> None:
        """Records verifiable satisfaction of an acceptance criterion."""
        for c in self.acceptance_criteria:
            if c.id == criterion_id:
                c.satisfied = True
                c.evidence = evidence
                c.evaluated_at = datetime.now(UTC)
                return
        raise KeyError(
            f"Acceptance criterion '{criterion_id}' not found in scenario '{self.scenario_id}'"
        )

    def register_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        content: str | bytes,
        version: int = 1,
        persisted: bool = False,
        retrievable: bool = False,
    ) -> ArtifactBinding:
        """Computes SHA-256 fingerprint and cryptographically binds the artifact."""
        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        digest = hashlib.sha256(raw_bytes).hexdigest()

        binding = ArtifactBinding(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            content_hash=digest,
            version=version,
            persisted=persisted,
            retrievable=retrievable,
            byte_size=len(raw_bytes),
        )
        self.artifact_bindings[artifact_id] = binding
        return binding

    def verify_artifact_binding(self, artifact_id: str, content: str | bytes) -> bool:
        """Verifies that an inspected artifact matches its registered SHA-256 hash."""
        if artifact_id not in self.artifact_bindings:
            raise ArtifactBindingError(f"No artifact binding registered for ID '{artifact_id}'")

        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        digest = hashlib.sha256(raw_bytes).hexdigest()
        registered_hash = self.artifact_bindings[artifact_id].content_hash

        if digest != registered_hash:
            raise ArtifactBindingError(
                f"Artifact binding mismatch for '{artifact_id}': expected SHA-256 {registered_hash[:12]}..., "
                f"got {digest[:12]}..."
            )
        return True

    def record_step(
        self,
        step_name: str,
        state: ExecutionState,
        details: dict[str, Any] | None = None,
        validation_notes: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> StepRecord:
        """Appends a completed step audit record."""
        rec = StepRecord(
            step_name=step_name,
            state=state,
            details=details or {},
            validation_notes=validation_notes or [],
            errors=errors or [],
        )
        self.steps.append(rec)
        return rec

    def transition_to(
        self,
        target_state: ExecutionState,
        reason: str,
        step_context: str | None = None,
    ) -> StateTransitionRecord:
        """Executes a validated state transition with quality gate enforcement."""
        # Allow idempotent re-validation on same state if context changes
        if target_state == self.current_state and target_state in (
            ExecutionState.STEP_VALIDATED,
            ExecutionState.STEP_EXECUTED,
            ExecutionState.REVIEW_REQUIRED,
        ):
            record = StateTransitionRecord(
                from_state=self.current_state,
                to_state=target_state,
                reason=reason,
                step_context=step_context,
            )
            self.transitions.append(record)
            return record

        # 1. Check legal transitions from current state
        allowed = self.VALID_TRANSITIONS.get(self.current_state, set())
        if target_state not in allowed:
            raise InvalidTransitionError(
                f"Invalid state transition from '{self.current_state.value}' to '{target_state.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}. Reason: {reason}"
            )

        # 2. Gate Checks for SUCCESS_FULLY_VERIFIED
        if target_state == ExecutionState.SUCCESS_FULLY_VERIFIED:
            self._validate_success_gates()

        # 3. Gate Checks for COMPLETED_WITH_WARNINGS
        if target_state == ExecutionState.COMPLETED_WITH_WARNINGS:
            self._validate_warnings_gates()

        # 4. Record transition
        record = StateTransitionRecord(
            from_state=self.current_state,
            to_state=target_state,
            reason=reason,
            step_context=step_context,
        )
        self.transitions.append(record)
        self.current_state = target_state

        if target_state in (
            ExecutionState.SUCCESS_FULLY_VERIFIED,
            ExecutionState.COMPLETED_WITH_WARNINGS,
            ExecutionState.BLOCKED,
            ExecutionState.FAILED,
        ):
            self.terminal_state = target_state

        return record

    def _validate_success_gates(self) -> None:
        """Strict release gate validations for SUCCESS_FULLY_VERIFIED."""
        # Condition A: All mandatory acceptance criteria must be satisfied
        unsatisfied = [c for c in self.acceptance_criteria if c.is_mandatory and not c.satisfied]
        if unsatisfied:
            criteria_list = ", ".join(f"'{c.id}: {c.description}'" for c in unsatisfied)
            raise GateValidationError(
                f"Cannot transition to SUCCESS_FULLY_VERIFIED: mandatory acceptance criteria unsatisfied: {criteria_list}"
            )

        # Condition B: Zero unresolved blocking findings
        blocking = [
            f
            for f in self.unresolved_findings
            if f.get("blocks_release", False) or f.get("severity") in ("critical", "high")
        ]
        if blocking:
            raise GateValidationError(
                f"Cannot transition to SUCCESS_FULLY_VERIFIED: {len(blocking)} blocking findings remain unresolved."
            )

        # Condition C: Non-blocking findings must not be present for 100% full verification
        if self.unresolved_findings:
            raise GateValidationError(
                f"Cannot transition to SUCCESS_FULLY_VERIFIED: {len(self.unresolved_findings)} non-blocking findings "
                "remain open. Transition to COMPLETED_WITH_WARNINGS instead."
            )

        # Condition D: Artifacts must be persisted and retrievable
        for art_id, binding in self.artifact_bindings.items():
            if not binding.persisted or not binding.retrievable:
                raise GateValidationError(
                    f"Cannot transition to SUCCESS_FULLY_VERIFIED: Artifact '{art_id}' is not persisted or retrievable."
                )

        # Condition E: Warnings list must be empty for full verification
        if self.warnings:
            raise GateValidationError(
                f"Cannot transition to SUCCESS_FULLY_VERIFIED: {len(self.warnings)} warnings present. "
                "Transition to COMPLETED_WITH_WARNINGS instead."
            )

        # Condition F: Evaluation records must not contain contradictory mock-as-live provenance
        self._validate_evaluation_provenance()

    def _validate_warnings_gates(self) -> None:
        """Gate validations for COMPLETED_WITH_WARNINGS."""
        # Condition A: Cannot complete with warnings if a CRITICAL or HIGH blocking issue remains
        blocking = [
            f
            for f in self.unresolved_findings
            if f.get("blocks_release", False) or f.get("severity") in ("critical", "high")
        ]
        if blocking:
            raise GateValidationError(
                f"Cannot transition to COMPLETED_WITH_WARNINGS: {len(blocking)} blocking findings remain unresolved. "
                "Scenario must transition to NEEDS_REVISION, BLOCKED, or FAILED."
            )

        # Condition B: Must have warning records if unresolved findings exist
        if self.unresolved_findings and not self.warnings:
            self.derive_unresolved_findings_and_warnings()
            if not self.warnings:
                raise GateValidationError(
                    "Cannot transition to COMPLETED_WITH_WARNINGS: unresolved findings exist but warnings list is empty."
                )

        # Condition C: Evaluation records must not contain contradictory mock-as-live provenance
        self._validate_evaluation_provenance()

    def _validate_evaluation_provenance(self) -> None:
        """Enforces that mock evaluations or synthetic routes are never classified as LIVE_PROVIDER."""
        for ev in self.evaluation_records:
            m_id = ev.get("model_id", "")
            route = str(ev.get("provider_route") or ev.get("provenance", {}).get("route", "")).lower()
            m_mode = str(ev.get("execution_mode", "")).upper()
            prov_mode = str(ev.get("provenance", {}).get("mode", "")).upper()

            is_mock = m_id in ("promptiq-mock-v1", "mock") or route in ("mock", "synthetic")

            if is_mock and (m_mode in ("LIVE", "LIVE_PROVIDER") or prov_mode in ("LIVE", "LIVE_PROVIDER")):
                raise GateValidationError(
                    f"Contradictory execution mode in evaluation record: model '{m_id}' on route '{route}' "
                    "cannot be classified as LIVE_PROVIDER."
                )

            if m_mode == "LIVE_PROVIDER":
                has_req_id = bool(ev.get("provider_request_id")) or any(
                    bool(r.get("provider_request_id")) for r in ev.get("results", [])
                )
                if not has_req_id:
                    raise GateValidationError(
                        "Evaluation record claims LIVE_PROVIDER execution mode without verifiable provider request ID."
                    )

    def to_audit_trace(self) -> ScenarioAuditTrace:
        """Exports the complete audit trace."""
        # Ensure warning records are synchronized
        if self.unresolved_findings and not self.warning_records:
            self.derive_unresolved_findings_and_warnings()

        return ScenarioAuditTrace(
            scenario_id=self.scenario_id,
            category=self.category,
            input_summary=self.input_summary,
            execution_mode=self.execution_mode,
            current_state=self.current_state,
            terminal_state=self.terminal_state,
            steps=self.steps,
            transitions=self.transitions,
            acceptance_criteria=self.acceptance_criteria,
            artifact_bindings=list(self.artifact_bindings.values()),
            initial_autopsy=self.initial_autopsy,
            revision_events=self.revision_events,
            resolution_events=self.resolution_events,
            final_autopsy=self.final_autopsy,
            autopsy_findings=self.autopsy_findings,
            unresolved_findings=self.unresolved_findings,
            evaluation_records=self.evaluation_records,
            warning_records=self.warning_records,
            warnings=self.warnings,
            blocking_reasons=self.blocking_reasons,
            execution_metadata=self.metadata,
        )
