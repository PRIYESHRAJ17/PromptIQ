"""Project Constitution domain service with immutable versioning and diffing."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import NotFoundError
from promptiq.models.audit import AuditEvent
from promptiq.models.constitution import ConstitutionVersion, ProjectConstitution
from promptiq.schemas.constitution import ConstitutionApprovalRequest, ConstitutionUpdate
from promptiq.services.project_service import ProjectService


class ConstitutionService:
    """Manages Project Constitution versions, approval gates, diffs, and rollback."""

    @classmethod
    async def get_current_constitution(
        cls, db: AsyncSession, project_id: str, user_id: str
    ) -> ProjectConstitution:
        """Retrieves the current active version of a project's constitution."""
        project = await ProjectService.get_project(db, project_id, user_id)

        stmt = select(ProjectConstitution).where(
            ProjectConstitution.project_id == project.id,
            ProjectConstitution.version == project.current_constitution_version,
        )
        res = await db.execute(stmt)
        constitution = res.scalar_one_or_none()
        if not constitution:
            # Fallback to highest version if pointer is unaligned
            fallback_stmt = (
                select(ProjectConstitution)
                .where(ProjectConstitution.project_id == project.id)
                .order_by(ProjectConstitution.version.desc())
            )
            res_fallback = await db.execute(fallback_stmt)
            constitution = res_fallback.scalar_one_or_none()

        if not constitution:
            raise NotFoundError(resource="ProjectConstitution", resource_id=project_id)

        return constitution

    @classmethod
    async def get_constitution_by_version(
        cls, db: AsyncSession, project_id: str, version: int, user_id: str
    ) -> ConstitutionVersion:
        """Retrieves an immutable snapshot of a specific constitution version."""
        await ProjectService.get_project(db, project_id, user_id)

        stmt = select(ConstitutionVersion).where(
            ConstitutionVersion.project_id == project_id,
            ConstitutionVersion.version == version,
        )
        res = await db.execute(stmt)
        version_record = res.scalar_one_or_none()
        if not version_record:
            raise NotFoundError(
                resource="ConstitutionVersion", resource_id=f"{project_id}/v{version}"
            )

        return version_record

    @classmethod
    def calculate_diff(cls, old_dict: dict[str, Any], new_dict: dict[str, Any]) -> dict[str, Any]:
        """Calculates granular additions, modifications, and deletions between two constitution states."""
        diff: dict[str, Any] = {"added": {}, "modified": {}, "removed": {}}

        all_keys = set(old_dict.keys()).union(set(new_dict.keys()))
        for key in all_keys:
            old_val = old_dict.get(key)
            new_val = new_dict.get(key)

            if old_val is None and new_val is not None:
                diff["added"][key] = new_val
            elif old_val is not None and new_val is None:
                diff["removed"][key] = old_val
            elif old_val != new_val:
                diff["modified"][key] = {"from": old_val, "to": new_val}

        return diff

    @classmethod
    async def update_constitution(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        update_in: ConstitutionUpdate,
        surface: str = "api",
    ) -> ProjectConstitution:
        """Applies updates to the Constitution, creating a new immutable version."""
        project = await ProjectService.get_project(db, project_id, user_id)
        current = await cls.get_current_constitution(db, project_id, user_id)

        # Snapshot of current state for diff calculation
        old_state = {
            "goals": current.goals,
            "requirements": current.requirements,
            "scope": current.scope,
            "ux_specs": current.ux_specs,
            "technical_direction": current.technical_direction,
            "decisions": current.decisions,
            "assumptions": current.assumptions,
            "open_questions": current.open_questions,
            "risks": getattr(current, "risks", []) or [],
            "conflicts": getattr(current, "conflicts", []) or [],
        }

        # Apply updates
        new_goals = update_in.goals if update_in.goals is not None else current.goals
        new_reqs = (
            [r.model_dump() for r in update_in.requirements]
            if update_in.requirements is not None
            else current.requirements
        )

        new_scope = (current.scope or {}).copy()
        if update_in.scope_in is not None:
            new_scope["in_scope"] = update_in.scope_in
        if update_in.scope_out is not None:
            new_scope["out_of_scope"] = update_in.scope_out

        new_ux = (
            update_in.ux_specs.model_dump() if update_in.ux_specs is not None else current.ux_specs
        )
        new_tech = (
            update_in.technical_direction.model_dump()
            if update_in.technical_direction is not None
            else current.technical_direction
        )
        new_decisions = (
            [d.model_dump() for d in update_in.decisions]
            if update_in.decisions is not None
            else current.decisions
        )
        new_assumptions = (
            [a.model_dump() for a in update_in.assumptions]
            if update_in.assumptions is not None
            else current.assumptions
        )
        new_questions = (
            [q.model_dump() for q in update_in.open_questions]
            if update_in.open_questions is not None
            else current.open_questions
        )
        new_risks = (
            [r.model_dump() for r in update_in.risks]
            if update_in.risks is not None
            else (getattr(current, "risks", []) or [])
        )
        new_conflicts = (
            [c.model_dump() for c in update_in.conflicts]
            if update_in.conflicts is not None
            else (getattr(current, "conflicts", []) or [])
        )

        new_state = {
            "goals": new_goals,
            "requirements": new_reqs,
            "scope": new_scope,
            "ux_specs": new_ux,
            "technical_direction": new_tech,
            "decisions": new_decisions,
            "assumptions": new_assumptions,
            "open_questions": new_questions,
            "risks": new_risks,
            "conflicts": new_conflicts,
        }

        diff = cls.calculate_diff(old_state, new_state)

        new_version_num = current.version + 1

        # Create new version record
        new_constitution = ProjectConstitution(
            project_id=project.id,
            version=new_version_num,
            status="draft",
            is_approved=False,  # Updating invalidates previous approval
            goals=new_goals,
            requirements=new_reqs,
            scope=new_scope,
            ux_specs=new_ux,
            technical_direction=new_tech,
            decisions=new_decisions,
            assumptions=new_assumptions,
            open_questions=new_questions,
            risks=new_risks,
            conflicts=new_conflicts,
            diff_from_previous=diff,
        )
        db.add(new_constitution)

        # Archive immutable snapshot
        snapshot_record = ConstitutionVersion(
            project_id=project.id,
            version=new_version_num,
            snapshot=new_state,
            diff=diff,
            created_by_user_id=user_id,
        )
        db.add(snapshot_record)

        # Advance project version pointer
        project.current_constitution_version = new_version_num

        # Audit log
        audit = AuditEvent(
            workspace_id=project.workspace_id,
            project_id=project.id,
            user_id=user_id,
            action="constitution.updated",
            surface=surface,
            payload={
                "new_version": new_version_num,
                "modified_fields": list(diff["modified"].keys()),
            },
        )
        db.add(audit)
        await db.flush()

        return new_constitution

    @classmethod
    async def approve_constitution(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        approval_in: ConstitutionApprovalRequest,
        surface: str = "api",
    ) -> ProjectConstitution:
        """Approve or reject the active Constitution version."""
        project = await ProjectService.get_project(db, project_id, user_id)
        current = await cls.get_current_constitution(db, project_id, user_id)

        if approval_in.approve:
            current.is_approved = True
            current.status = "approved"
            current.approved_by_user_id = user_id
            action = "constitution.approved"
        else:
            current.is_approved = False
            current.status = "rejected"
            action = "constitution.rejected"

        audit = AuditEvent(
            workspace_id=project.workspace_id,
            project_id=project.id,
            user_id=user_id,
            action=action,
            surface=surface,
            payload={
                "version": current.version,
                "approved": approval_in.approve,
                "feedback": approval_in.feedback,
            },
        )
        db.add(audit)
        await db.flush()
        return current

    @classmethod
    async def compare_versions(
        cls,
        db: AsyncSession,
        project_id: str,
        v1: int,
        v2: int,
        user_id: str,
    ) -> dict[str, Any]:
        """Calculates granular additions, modifications, and deletions between two historical versions."""
        rec1 = await cls.get_constitution_by_version(db, project_id, v1, user_id)
        rec2 = await cls.get_constitution_by_version(db, project_id, v2, user_id)
        diff = cls.calculate_diff(rec1.snapshot or {}, rec2.snapshot or {})
        return {
            "project_id": project_id,
            "v1": v1,
            "v2": v2,
            "diff": diff,
        }

    @classmethod
    async def rollback_to_version(
        cls,
        db: AsyncSession,
        project_id: str,
        target_version: int,
        user_id: str,
        surface: str = "api",
    ) -> ProjectConstitution:
        """Rolls back the constitution to the state of target_version, producing a new immutable version N+1."""
        project = await ProjectService.get_project(db, project_id, user_id)
        current = await cls.get_current_constitution(db, project_id, user_id)
        target_record = await cls.get_constitution_by_version(
            db, project_id, target_version, user_id
        )

        old_state = {
            "goals": current.goals or [],
            "requirements": current.requirements or [],
            "scope": current.scope or {},
            "ux_specs": current.ux_specs or {},
            "technical_direction": current.technical_direction or {},
            "decisions": current.decisions or [],
            "assumptions": current.assumptions or [],
            "open_questions": current.open_questions or [],
        }

        target_state = target_record.snapshot or {}
        new_goals = target_state.get("goals", [])
        new_reqs = target_state.get("requirements", [])
        new_scope = target_state.get("scope", {})
        new_ux = target_state.get("ux_specs", {})
        new_tech = target_state.get("technical_direction", {})
        new_decisions = target_state.get("decisions", [])
        new_assumptions = target_state.get("assumptions", [])
        new_questions = target_state.get("open_questions", [])

        new_state = {
            "goals": new_goals,
            "requirements": new_reqs,
            "scope": new_scope,
            "ux_specs": new_ux,
            "technical_direction": new_tech,
            "decisions": new_decisions,
            "assumptions": new_assumptions,
            "open_questions": new_questions,
        }

        diff = cls.calculate_diff(old_state, new_state)
        new_version_num = current.version + 1

        new_constitution = ProjectConstitution(
            project_id=project.id,
            version=new_version_num,
            status="draft",
            is_approved=False,
            goals=new_goals,
            requirements=new_reqs,
            scope=new_scope,
            ux_specs=new_ux,
            technical_direction=new_tech,
            decisions=new_decisions,
            assumptions=new_assumptions,
            open_questions=new_questions,
            risks=new_state.get("risks", []),
            conflicts=new_state.get("conflicts", []),
            diff_from_previous=diff,
        )
        db.add(new_constitution)

        snapshot_record = ConstitutionVersion(
            project_id=project.id,
            version=new_version_num,
            snapshot=new_state,
            diff=diff,
            created_by_user_id=user_id,
        )
        db.add(snapshot_record)

        project.current_constitution_version = new_version_num

        audit = AuditEvent(
            workspace_id=project.workspace_id,
            project_id=project.id,
            user_id=user_id,
            action="constitution.reverted",
            surface=surface,
            payload={
                "target_version": target_version,
                "new_version": new_version_num,
                "modified_fields": list(diff.get("modified", {}).keys()),
            },
        )
        db.add(audit)
        await db.flush()
        return new_constitution

    @classmethod
    def get_requirement_traceability_matrix(
        cls, constitution: ProjectConstitution
    ) -> list[dict[str, Any]]:
        """Constructs an end-to-end traceability matrix linking requirements to verification states and deliverables."""
        matrix: list[dict[str, Any]] = []
        for req in constitution.requirements or []:
            if isinstance(req, dict):
                req_id = req.get("id")
                text = req.get("text", "")
                cat = req.get("category", "functional")
                prio = req.get("priority", "P1")
                status = req.get("status", "confirmed")
                prov = req.get("provenance", "user_provided")
                depends = req.get("depends_on", [])
                rels = req.get("relationships", [])
                target = req.get("deliverable_target")
                method = req.get("verification_method", "deterministic_test")
                v_status = req.get("verification_status", "unverified")
                gaps = req.get("outstanding_gaps", [])
            else:
                req_id = getattr(req, "id", None)
                text = getattr(req, "text", "")
                cat = getattr(req, "category", "functional")
                prio = getattr(req, "priority", "P1")
                status = getattr(req, "status", "confirmed")
                prov = getattr(req, "provenance", "user_provided")
                depends = getattr(req, "depends_on", [])
                rels = getattr(req, "relationships", [])
                target = getattr(req, "deliverable_target", None)
                method = getattr(req, "verification_method", "deterministic_test")
                v_status = getattr(req, "verification_status", "unverified")
                gaps = getattr(req, "outstanding_gaps", [])

            matrix.append(
                {
                    "id": req_id,
                    "text": text,
                    "category": cat,
                    "priority": prio,
                    "status": status,
                    "provenance": prov,
                    "depends_on": depends,
                    "relationships": rels,
                    "deliverable_target": target,
                    "verification_method": method,
                    "verification_status": v_status,
                    "outstanding_gaps": gaps,
                }
            )
        return matrix

    @classmethod
    def detect_prompt_contradictions(
        cls, constitution: ProjectConstitution, prompt_text: str
    ) -> list[str]:
        """Validates prompt text against Constitution scope, technical direction, and core project invariants."""
        contradictions: list[str] = []
        prompt_lower = (prompt_text or "").lower()

        # 1. Out of scope violations
        scope = constitution.scope or {}
        out_of_scope = scope.get("out_of_scope", [])
        for item in out_of_scope:
            item_clean = item.lower().strip()
            if item_clean and item_clean in prompt_lower:
                contradictions.append(
                    f"Prompt mentions explicitly excluded out-of-scope element: '{item}'"
                )

        # 2. Prohibited technology stack violations
        tech_dir = constitution.technical_direction or {}
        prohibited = tech_dir.get("prohibited_stack", [])
        for tech in prohibited:
            tech_clean = tech.lower().strip()
            if tech_clean and tech_clean in prompt_lower:
                contradictions.append(
                    f"Prompt references prohibited technology stack item: '{tech}'"
                )

        # 3. Core Invariant 1: Strictly No Website Frontend
        frontend_keywords = [
            "react",
            "vue",
            "next.js",
            "nextjs",
            "angular",
            "html page",
            "tailwind ui",
            "frontend page",
        ]
        has_frontend_exclusion = any(
            "no frontend" in item.lower() or "backend only" in item.lower() for item in out_of_scope
        )
        if has_frontend_exclusion or True:  # Core PromptIQ Invariant
            for kw in frontend_keywords:
                if (
                    f"build {kw}" in prompt_lower
                    or f"create {kw}" in prompt_lower
                    or f"generate {kw}" in prompt_lower
                ):
                    contradictions.append(
                        f"Prompt requests generating website frontend ({kw}), violating strict backend-only invariant."
                    )
                    break

        # 4. Core Invariant 2: Zero User API Keys / No BYOK
        if (
            "user api key" in prompt_lower
            or "enter your openai key" in prompt_lower
            or "byok" in prompt_lower
        ):
            contradictions.append(
                "Prompt requests user API key input, violating PromptIQ's zero-price / zero-BYOK invariant."
            )

        # 5. Core Invariant 3: No Local Inference
        if (
            "install ollama" in prompt_lower
            or "run llama.cpp" in prompt_lower
            or "local gpu inference" in prompt_lower
        ):
            contradictions.append(
                "Prompt requires local inference tools, violating centrally managed hosted gateway invariant."
            )

        return contradictions
