"""Requirement Traceability and Coverage Verification Engine."""

from typing import Any

from pydantic import BaseModel, Field

from promptiq.orchestrator.planner import ExecutionPlan, SubtaskStatus


class RequirementTraceItem(BaseModel):
    requirement_id: str
    priority: str  # P0, P1, P2, P3
    text: str
    category: str = "functional"
    associated_subtask_id: str | None = None
    execution_status: str = "UNVERIFIED"  # VERIFIED, UNVERIFIED, FAILED, WAIVED
    verification_method: str = "deterministic_assertion"
    supporting_evidence: str | None = None
    remaining_uncertainty: str = "NONE"  # NONE, LOW, MEDIUM, HIGH


class RequirementCoverageReport(BaseModel):
    project_id: str
    constitution_version: int
    total_requirements: int
    verified_count: int
    failed_count: int
    p0_p1_coverage_percent: float = Field(ge=0.0, le=100.0)
    is_release_approved: bool
    blocking_unresolved_requirements: list[str] = Field(default_factory=list)
    items: list[RequirementTraceItem] = Field(default_factory=list)


class RequirementTraceabilityEngine:
    """Verifies that every critical project requirement is executed, verified, and traceable to the final deliverable."""

    @classmethod
    def compute_coverage(
        cls,
        project_id: str,
        constitution_version: int,
        requirements: list[dict[str, Any]],
        plan: ExecutionPlan | None = None,
        test_results: dict[str, Any] | None = None,
        deliverable_text: str | None = None,
    ) -> RequirementCoverageReport:
        """Calculates requirement coverage, verifies P0/P1 delivery, and determines release approval."""
        items: list[RequirementTraceItem] = []
        blocking: list[str] = []
        verified_count = 0
        failed_count = 0

        p0_p1_total = 0
        p0_p1_verified = 0

        plan_subtasks = {t.id: t for t in (plan.subtasks if plan else [])}
        deliverable = deliverable_text or ""

        for req in requirements:
            req_id = req.get("id", "REQ-UNKNOWN")
            priority = req.get("priority", "P1").upper()
            text = req.get("text", "")
            category = req.get("category", "functional")

            is_p0_p1 = priority in ("P0", "P1")
            if is_p0_p1:
                p0_p1_total += 1

            # Determine associated subtask
            assoc_subtask_id: str | None = None
            if plan:
                # Match by keyword or default generation task
                for st in plan.subtasks:
                    if any(
                        w in st.objective.lower() for w in text.lower().split()[:3] if len(w) > 3
                    ):
                        assoc_subtask_id = st.id
                        break
                if not assoc_subtask_id:
                    assoc_subtask_id = "task-04-generate"

            # Check verification status
            status = "UNVERIFIED"
            evidence = None
            method = "deliverable_containment"

            # 1. Check if associated subtask completed
            st_node = plan_subtasks.get(assoc_subtask_id) if assoc_subtask_id else None
            subtask_completed = st_node.status == SubtaskStatus.COMPLETED if st_node else False

            # 2. Check if content or intent is present in deliverable
            req_keywords = [
                w.lower()
                for w in text.split()
                if len(w) > 3 and w.lower() not in ("must", "should", "shall", "include")
            ]
            keyword_matches = (
                sum(1 for kw in req_keywords if kw in deliverable.lower()) if req_keywords else 1
            )
            content_supported = (
                keyword_matches >= max(1, len(req_keywords) // 2) if req_keywords else True
            )

            # 3. Check Test Lab assertions if available
            test_passed = True
            if test_results:
                test_passed = test_results.get("all_passed", True)

            if subtask_completed and content_supported and test_passed:
                status = "VERIFIED"
                verified_count += 1
                if is_p0_p1:
                    p0_p1_verified += 1
                evidence = f"Subtask '{assoc_subtask_id}' completed with {keyword_matches}/{len(req_keywords)} keywords reflected in deliverable."
            else:
                status = (
                    "FAILED"
                    if (st_node and st_node.status == SubtaskStatus.FAILED)
                    else "UNVERIFIED"
                )
                failed_count += 1
                if is_p0_p1:
                    blocking.append(f"{req_id} ({priority}): {text[:60]}")
                evidence = f"Incomplete verification: subtask_status={st_node.status.value if st_node else 'none'}, content_supported={content_supported}"

            items.append(
                RequirementTraceItem(
                    requirement_id=req_id,
                    priority=priority,
                    text=text,
                    category=category,
                    associated_subtask_id=assoc_subtask_id,
                    execution_status=status,
                    verification_method=method,
                    supporting_evidence=evidence,
                    remaining_uncertainty="NONE"
                    if status == "VERIFIED"
                    else ("HIGH" if is_p0_p1 else "MEDIUM"),
                )
            )

        p0_p1_coverage = (p0_p1_verified / p0_p1_total * 100.0) if p0_p1_total > 0 else 100.0
        # Release is approved ONLY if all P0/P1 requirements are verified (100% coverage on critical path)
        is_approved = (len(blocking) == 0) and (p0_p1_coverage >= 100.0)

        return RequirementCoverageReport(
            project_id=project_id,
            constitution_version=constitution_version,
            total_requirements=len(requirements),
            verified_count=verified_count,
            failed_count=failed_count,
            p0_p1_coverage_percent=round(p0_p1_coverage, 2),
            is_release_approved=is_approved,
            blocking_unresolved_requirements=blocking,
            items=items,
        )
