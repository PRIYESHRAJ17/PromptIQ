# PromptIQ — Engineering Issue Ledger & Root-Cause Analysis

**Audit Baseline**: Commit `f2b15fd`  
**Date**: 2026-11-22  
**Auditor**: Principal Systems Architect & Quality Engineering Lead  

---

## 1. Summary of Discovered Defects

| Issue ID | Severity | Impacted Module | Root Cause Summary | Required Correction | Target Phase | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | **CRITICAL** | `promptiq/schemas/acceptance.py`, `state_machine.py` | Historical autopsy finding status (`pending`) conflicted with resolved state; `autopsy_findings` not updated | Separate immutable historical snapshots (`initial_autopsy`) from current findings ledger; update disposition on resolution; enhance `FindingResolutionEvent` | Phase B | **RESOLVED** |
| **ISSUE-002** | **HIGH** | `promptiq/schemas/acceptance.py`, `runner.py` | Criteria marked satisfied with prose strings lacking verifiable references | Add structured evidence fields (`evidence_record_type`, `evidence_reference`, `verifiable_data`); enforce non-empty verifiable references | Phase B | **RESOLVED** |
| **ISSUE-003** | **HIGH** | `promptiq/acceptance/state_machine.py` | Warning strings and structured `WarningRecord`s out of sync (Scenario 2 had 1 warning, 0 records) | Enforce bidirectional warning consistency; generate `WarningRecord` for execution warnings | Phase B | **RESOLVED** |
| **ISSUE-004** | **MEDIUM** | `promptiq/schemas/acceptance.py`, `state_machine.py` | `StepRecord` lacked explicit duration measurement (`duration_ms`) and monotonic clock tracking | Add `duration_ms` to `StepRecord`; record monotonic start/end times with `started_at <= completed_at` | Phase B | **RESOLVED** |
| **ISSUE-005** | **HIGH** | `promptiq/critic/autopsy.py` | Autopsy inspected only 9 categories out of 21 mandated in technical specification | Implement comprehensive static/heuristic critique for all 21 categories with evidence passages | Phase F | **RESOLVED** |
| **ISSUE-006** | **MEDIUM** | `promptiq/schemas/research.py`, `engine.py` | Research claim support taxonomy incomplete (missing `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `UNVERIFIED`) | Expand `support_status` literal and update claim evaluation logic | Phase I | **RESOLVED** |
| **ISSUE-007** | **HIGH** | `promptiq/acceptance/validator.py` (New) | No independent trace validator existed separate from the trace runner generator | Implement `AcceptanceTraceValidator` verifying hashes, persisted DB records, timings, and tenant boundaries | Phase P | **RESOLVED** |
| **ISSUE-008** | **MEDIUM** | `promptiq/telegram/bot.py` | Telegram webhook deduplication was in-memory only, vulnerable to multi-worker restarts | Implement persistent database-backed or durable storage deduplication for Telegram update IDs | Phase K | **RESOLVED** |
| **ISSUE-009** | **HIGH** | `promptiq/telegram/`, `models/telegram.py`, `validator.py` | File-backed Telegram deduplication unsafe for multi-worker concurrency; trace criteria allowed unresolvable artifact IDs/hashes | Implement database-backed `TelegramProcessedUpdate` with Alembic migration `0002`, transaction savepoints, and stress tests; add strict evidence reference resolution to validator | Post-Commit Audit | **RESOLVED** |

---

## 2. Detailed Root-Cause & Remediation Plan

### ISSUE-001: Historical Autopsy Finding State vs Current Finding Ledger Inconsistency
- **Severity**: CRITICAL
- **Impacted Modules**: `promptiq/schemas/acceptance.py`, `promptiq/acceptance/state_machine.py`, `promptiq/acceptance/runner.py`
- **Reproduction**: In `docs/ACCEPTANCE_SCENARIOS_TRACE_V3.json` Scenario 1:
  - `initial_autopsy` contains `FINDING-527dc08e` (`missing_error_handling`, `disposition: "pending"`, `is_resolved: false`).
  - `resolution_events` contains `RES-30bc0269` resolving `FINDING-527dc08e`.
  - `unresolved_findings` is empty `[]`.
  - BUT `autopsy_findings` still contains `FINDING-527dc08e` with `disposition: "pending"` and `is_resolved: false`!
- **Root Cause**: `AcceptanceStateMachine.record_finding_resolution()` appends to `resolution_events` and derives `unresolved_findings`, but fails to update the active status in `autopsy_findings` (the current findings ledger). Furthermore, `FindingResolutionEvent` schema lacks `original_artifact_id`, `revised_artifact_id`, and `verification_method`.
- **Required Correction**:
  1. Add `original_artifact_id`, `revised_artifact_id`, and `verification_method` to `FindingResolutionEvent`.
  2. In `record_finding_resolution()`, locate the finding in `self.autopsy_findings` and update `disposition = status`, `is_resolved = True`, `resolution_id = res.resolution_id`.
  3. Ensure `initial_autopsy` remains an immutable historical record retaining the original `disposition: "pending"`.
- **Regression Test**: Test in `tests/test_acceptance_integrity_negative.py` asserting that after recording a resolution, `autopsy_findings` reflects `is_resolved=True` while `initial_autopsy` retains `is_resolved=False`.

---

### ISSUE-002: Acceptance Criteria Satisfied Without Independently Verifiable Evidence References
- **Severity**: HIGH
- **Impacted Modules**: `promptiq/schemas/acceptance.py`, `promptiq/acceptance/state_machine.py`, `promptiq/acceptance/runner.py`
- **Reproduction**: `AcceptanceCriterion` contains only `evidence: str | None = None`. Criteria can be marked satisfied with descriptive English sentences without referencing an artifact ID, content hash, database record ID, provider request ID, or test execution ID.
- **Root Cause**: Schema did not define structured reference fields, and `mark_criterion_satisfied` only took a single string argument.
- **Required Correction**:
  1. Add `evidence_record_type: str | None = None` (e.g. `"artifact"`, `"hash"`, `"db_record"`, `"eval_run"`, `"provider_request"`).
  2. Add `evidence_reference: str | None = None` (e.g. artifact ID, SHA-256 hash, DB primary key).
  3. Add `verifiable_data: dict[str, Any] | None = None`.
  4. Update `mark_criterion_satisfied` to accept and validate these structured references.
  5. In state machine validation, reject marking mandatory criteria satisfied without verifiable references.
- **Regression Test**: Negative test attempting to mark a mandatory criterion satisfied with a blank or null `evidence_reference`.

---

### ISSUE-003: Warning Record and Warning String Array Inconsistency
- **Severity**: HIGH
- **Impacted Modules**: `promptiq/acceptance/state_machine.py`, `promptiq/schemas/acceptance.py`
- **Reproduction**: In Scenario 2, `warnings` contains 1 item (`"Evidence ledger contains simulated research citations; live internet search was unverified"`), but `warning_records` has 0 items.
- **Root Cause**: Warnings added via `sm.warnings.append(...)` or stage transitions bypassed `warning_records`.
- **Required Correction**: Provide `add_warning(warning_text, category, severity, finding_id=None)` on `AcceptanceStateMachine` that atomically updates both `warnings: list[str]` and `warning_records: list[WarningRecord]`. Enforce bidirectional matching in transition validators.
- **Regression Test**: Test verifying that len(warnings) == len(warning_records) across all states.

---

### ISSUE-004: Missing Step Duration Measurement and Timing Integrity
- **Severity**: MEDIUM
- **Impacted Modules**: `promptiq/schemas/acceptance.py`, `promptiq/acceptance/state_machine.py`
- **Reproduction**: `StepRecord` had identical `started_at` and `completed_at` values and no `duration_ms` attribute.
- **Root Cause**: `StepRecord` lacked a duration field, and runner did not wrap steps in monotonic timers.
- **Required Correction**:
  1. Add `duration_ms: float | None = None` to `StepRecord`.
  2. Add `sm.begin_step(name)` and `sm.complete_step(name)` (or context manager `sm.step_context(name)`) using `time.perf_counter()` to record accurate duration and verify `started_at <= completed_at`.
- **Regression Test**: Test asserting all steps have non-negative `duration_ms` and valid chronological order.

---

### ISSUE-005: Incomplete Prompt Autopsy Heuristic Inspection Categories
- **Severity**: HIGH
- **Impacted Module**: `promptiq/critic/autopsy.py`
- **Reproduction**: Only 9 inspection categories were registered.
- **Root Cause**: Incremental implementation left 12 categories unimplemented.
- **Required Correction**: Implement inspection logic for all 21 categories:
  - `ambiguity`, `vagueness`, `missing_requirements`, `contradictions`, `incomplete_context`, `missing_negative_constraints`, `unsafe_permissions`, `excessive_agency`, `prompt_injection`, `system_instruction_extraction`, `tool_misuse`, `missing_error_handling`, `missing_stop_conditions`, `missing_output_schema`, `missing_testability`, `unsupported_claims`, `privacy_violations`, `data_classification_conflicts`, `target_incompatibilities`, `excessive_context`, `unnecessary_complexity`.
- **Regression Test**: Test exercising each of the 21 categories with targeted test prompts.

---

### ISSUE-006: Incomplete Research Claim Support Taxonomy
- **Severity**: MEDIUM
- **Impacted Modules**: `promptiq/schemas/research.py`, `promptiq/research/engine.py`
- **Reproduction**: Literal only supported `SUPPORTED`, `CONTRADICTED`, `INCONCLUSIVE`.
- **Root Cause**: Limited literal definition.
- **Required Correction**: Expand to `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `UNSUPPORTED`, `UNVERIFIED`.
- **Regression Test**: Test validating claim evaluation with all 5 support statuses.

---

### ISSUE-007: Absence of Independent Acceptance Trace Validator
- **Severity**: HIGH
- **Impacted Module**: `promptiq/acceptance/validator.py` (New)
- **Reproduction**: No independent validator exists to verify `ACCEPTANCE_SCENARIOS_TRACE_V4.json` against database state, content hashes, and structural rules.
- **Root Cause**: Architectural omission; the generator validated itself.
- **Required Correction**: Create `AcceptanceTraceValidator` that independently loads trace V4, inspects actual SQLite database tables, recomputes artifact hashes from disk/DB, checks tenant boundaries, verifies step ordering, and checks criterion evidence references.
- **Regression Test**: Comprehensive negative tests suite testing 20+ violation conditions against the validator.

---

### ISSUE-008: Ephemeral In-Memory Deduplication in Telegram Bot
- **Severity**: MEDIUM
- **Impacted Module**: `promptiq/telegram/bot.py`, `promptiq/models/`
- **Reproduction**: Restarting the backend server clears the processed update IDs set, allowing duplicate webhook deliveries to be re-processed.
- **Root Cause**: Deduplication was stored in an in-memory set.
- **Required Correction**: Add persistent storage for processed Telegram `update_id`s in the database (or durable SQLite table `telegram_processed_updates`).
- **Regression Test**: Test verifying that update IDs survive client re-instantiation.

---

### ISSUE-009: File-Backed Telegram Deduplication Concurrency Risk & Unresolvable Trace Evidence
- **Severity**: HIGH
- **Impacted Modules**: `promptiq/telegram/bot.py`, `promptiq/models/telegram.py`, `promptiq/acceptance/validator.py`, `alembic/versions/`
- **Reproduction**: 
  1. A raw JSON file (`data/telegram_updates.json`) lacks atomic row-level locks, leading to race conditions under concurrent webhook deliveries, file corruption on interrupted writes, and failure across multi-process workers or containerized instances without shared storage.
  2. Acceptance criteria evidence containing unresolvable artifact IDs or hashes could pass if the validator only performed syntactic regex matching.
- **Root Cause**:
  - File-based deduplication is unsuitable for distributed or multi-worker production environments.
  - Trace validator checked pattern formats (e.g. 64-char hex) but did not cross-reference against actual `artifact_bindings`.
- **Required Correction**:
  1. Created SQLAlchemy model `TelegramProcessedUpdate` and Alembic migration `a1b2c3d4e5f6_0002_add_telegram_processed_updates.py`.
  2. Upgraded `TelegramBotClient.is_duplicate_update` with an atomic nested transaction (`begin_nested()`) catching `IntegrityError` on unique constraint conflict, backed by a high-speed L1 cache.
  3. Added `tests/test_telegram_dedup_concurrency.py` with 6 stress tests: concurrent duplicate updates, concurrent independent updates, multi-session worker sync, process restart resilience, corrupted file tolerance, and multi-instance shared database synchronization.
  4. Enhanced `AcceptanceTraceValidator.validate_acceptance_criteria` to resolve all referenced artifact IDs and 64-char hashes against `scenario["artifact_bindings"]`, rejecting unresolvable references. Added negative tests #22 and #23.
- **Verification Evidence**: 6 concurrency stress tests passing in 0.53s; 24 negative validator tests passing; Alembic migration upgrade/downgrade cycle tested and passing.
