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
    async def get_current_constitution(cls, db: AsyncSession, project_id: str, user_id: str) -> ProjectConstitution:
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
            fallback_stmt = select(ProjectConstitution).where(
                ProjectConstitution.project_id == project.id
            ).order_by(ProjectConstitution.version.desc())
            res_fallback = await db.execute(fallback_stmt)
            constitution = res_fallback.scalar_one_or_none()

        if not constitution:
            raise NotFoundError(resource="ProjectConstitution", resource_id=project_id)

        return constitution

    @classmethod
    async def get_constitution_by_version(cls, db: AsyncSession, project_id: str, version: int, user_id: str) -> ConstitutionVersion:
        """Retrieves an immutable snapshot of a specific constitution version."""
        await ProjectService.get_project(db, project_id, user_id)

        stmt = select(ConstitutionVersion).where(
            ConstitutionVersion.project_id == project_id,
            ConstitutionVersion.version == version,
        )
        res = await db.execute(stmt)
        version_record = res.scalar_one_or_none()
        if not version_record:
            raise NotFoundError(resource="ConstitutionVersion", resource_id=f"{project_id}/v{version}")

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
        }

        # Apply updates
        new_goals = update_in.goals if update_in.goals is not None else current.goals
        new_reqs = [r.model_dump() for r in update_in.requirements] if update_in.requirements is not None else current.requirements

        new_scope = (current.scope or {}).copy()
        if update_in.scope_in is not None:
            new_scope["in_scope"] = update_in.scope_in
        if update_in.scope_out is not None:
            new_scope["out_of_scope"] = update_in.scope_out

        new_ux = update_in.ux_specs.model_dump() if update_in.ux_specs is not None else current.ux_specs
        new_tech = update_in.technical_direction.model_dump() if update_in.technical_direction is not None else current.technical_direction
        new_decisions = [d.model_dump() for d in update_in.decisions] if update_in.decisions is not None else current.decisions
        new_assumptions = [a.model_dump() for a in update_in.assumptions] if update_in.assumptions is not None else current.assumptions
        new_questions = [q.model_dump() for q in update_in.open_questions] if update_in.open_questions is not None else current.open_questions

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
            payload={"new_version": new_version_num, "modified_fields": list(diff["modified"].keys())},
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
            payload={"version": current.version, "approved": approval_in.approve, "feedback": approval_in.feedback},
        )
        db.add(audit)
        await db.flush()
        return current
