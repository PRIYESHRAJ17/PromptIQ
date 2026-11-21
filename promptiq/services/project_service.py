"""Project management and tenant isolation service."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import NotFoundError, TenantIsolationError
from promptiq.models.audit import AuditEvent
from promptiq.models.constitution import ConstitutionVersion, ProjectConstitution
from promptiq.models.project import Project, ProjectMembership
from promptiq.models.user import WorkspaceMembership
from promptiq.schemas.project import ProjectCreate


class ProjectService:
    """Manages project lifecycle, multi-tenant isolation, and initial constitution setup."""

    @staticmethod
    async def verify_workspace_access(
        db: AsyncSession, user_id: str, workspace_id: str
    ) -> WorkspaceMembership:
        """Verifies that the user has valid membership in the specified workspace."""
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.workspace_id == workspace_id,
        )
        res = await db.execute(stmt)
        membership = res.scalar_one_or_none()
        if not membership:
            raise TenantIsolationError(
                f"User '{user_id}' does not have access to workspace '{workspace_id}'"
            )
        return membership

    @classmethod
    async def create_project(
        cls, db: AsyncSession, user_id: str, project_in: ProjectCreate, surface: str = "api"
    ) -> Project:
        """Creates a project with an initialized draft Project Constitution."""
        # Resolve target workspace
        workspace_id = project_in.workspace_id
        if not workspace_id:
            # Fall back to user's first owned workspace
            stmt = select(WorkspaceMembership).where(
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.role == "owner",
            )
            res = await db.execute(stmt)
            default_ws = res.scalar_one_or_none()
            if not default_ws:
                raise TenantIsolationError("No active workspace found for user")
            workspace_id = default_ws.workspace_id
        else:
            await cls.verify_workspace_access(db, user_id, workspace_id)

        project = Project(
            workspace_id=workspace_id,
            name=project_in.name,
            description=project_in.description,
            created_by_user_id=user_id,
            current_constitution_version=1,
            visibility=project_in.visibility,
        )
        db.add(project)
        await db.flush()

        # Add owner project membership
        proj_member = ProjectMembership(
            project_id=project.id,
            user_id=user_id,
            role="admin",
        )
        db.add(proj_member)

        # Initialize canonical draft ProjectConstitution
        initial_constitution = ProjectConstitution(
            project_id=project.id,
            version=1,
            status="draft",
            is_approved=False,
            goals=[project.description] if project.description else ["Build software project"],
            requirements=[],
            scope={"in_scope": [], "out_of_scope": []},
            ux_specs={},
            technical_direction={"preferred_stack": [], "architecture_pattern": "modular_monolith"},
            decisions=[],
            assumptions=[],
            open_questions=[],
            diff_from_previous={"created": "initial_draft"},
        )
        db.add(initial_constitution)
        await db.flush()

        # Create initial immutable version snapshot
        snapshot = {
            "version": 1,
            "status": "draft",
            "goals": initial_constitution.goals,
            "requirements": initial_constitution.requirements,
            "scope": initial_constitution.scope,
            "ux_specs": initial_constitution.ux_specs,
            "technical_direction": initial_constitution.technical_direction,
            "decisions": initial_constitution.decisions,
            "assumptions": initial_constitution.assumptions,
            "open_questions": initial_constitution.open_questions,
        }
        version_record = ConstitutionVersion(
            project_id=project.id,
            version=1,
            snapshot=snapshot,
            diff={"created": "initial_draft"},
            created_by_user_id=user_id,
        )
        db.add(version_record)

        # Log audit event
        audit = AuditEvent(
            workspace_id=workspace_id,
            project_id=project.id,
            user_id=user_id,
            action="project.created",
            surface=surface,
            payload={"name": project.name, "initial_version": 1},
        )
        db.add(audit)
        await db.flush()

        return project

    @classmethod
    async def get_project(cls, db: AsyncSession, project_id: str, user_id: str) -> Project:
        """Retrieves a project enforcing workspace tenant boundaries."""
        stmt = select(Project).where(Project.id == project_id)
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            raise NotFoundError(resource="Project", resource_id=project_id)

        # Verify tenant access
        await cls.verify_workspace_access(db, user_id, project.workspace_id)
        return project

    @classmethod
    async def list_projects(
        cls, db: AsyncSession, user_id: str, workspace_id: str | None = None
    ) -> list[Project]:
        """Lists all projects in the workspace accessible to the user."""
        if workspace_id:
            await cls.verify_workspace_access(db, user_id, workspace_id)
            stmt = (
                select(Project)
                .where(Project.workspace_id == workspace_id)
                .order_by(Project.created_at.desc())
            )
        else:
            # Query all workspaces the user belongs to
            ws_stmt = select(WorkspaceMembership.workspace_id).where(
                WorkspaceMembership.user_id == user_id
            )
            res_ws = await db.execute(ws_stmt)
            allowed_ws_ids = res_ws.scalars().all()
            if not allowed_ws_ids:
                return []
            stmt = (
                select(Project)
                .where(Project.workspace_id.in_(allowed_ws_ids))
                .order_by(Project.created_at.desc())
            )

        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def delete_project(
        cls, db: AsyncSession, project_id: str, user_id: str, surface: str = "api"
    ) -> bool:
        """Deletes a project and cleanly cascades through all dependent records after validating tenant boundaries."""
        project = await cls.get_project(db, project_id, user_id)
        workspace_id = project.workspace_id

        # 1. Cleanly delete dependent research jobs & evidence claims
        from promptiq.models.research import EvidenceClaim, ResearchJob, SourceRecord

        stmt_res = select(ResearchJob.id).where(ResearchJob.project_id == project.id)
        res_res = await db.execute(stmt_res)
        job_ids = list(res_res.scalars().all())
        if job_ids:
            await db.execute(
                delete(EvidenceClaim).where(EvidenceClaim.research_job_id.in_(job_ids))
            )
            await db.execute(delete(SourceRecord).where(SourceRecord.research_job_id.in_(job_ids)))
            await db.execute(delete(ResearchJob).where(ResearchJob.project_id == project.id))

        # 2. Cleanly delete dependent evaluation suites, runs, and failure records
        from promptiq.models.eval import EvaluationRun, EvaluationSuite, FailureRecord

        stmt_suite = select(EvaluationSuite.id).where(EvaluationSuite.project_id == project.id)
        res_suite = await db.execute(stmt_suite)
        suite_ids = list(res_suite.scalars().all())
        if suite_ids:
            await db.execute(delete(EvaluationRun).where(EvaluationRun.suite_id.in_(suite_ids)))
            await db.execute(
                delete(EvaluationSuite).where(EvaluationSuite.project_id == project.id)
            )

        await db.execute(delete(FailureRecord).where(FailureRecord.project_id == project.id))
        await db.execute(
            delete(ConstitutionVersion).where(ConstitutionVersion.project_id == project.id)
        )

        await db.delete(project)

        # Log audit trail
        audit = AuditEvent(
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            action="project.deleted",
            surface=surface,
            payload={"project_id": project_id},
        )
        db.add(audit)
        await db.flush()
        return True

    @classmethod
    async def export_project_data(
        cls, db: AsyncSession, project_id: str, user_id: str
    ) -> dict[str, Any]:
        """Gathers all project artifacts, memory, discovery sessions, constitutions, and packages into a single export."""
        project = await cls.get_project(db, project_id, user_id)

        # 1. Constitutions
        stmt_const = (
            select(ProjectConstitution)
            .where(ProjectConstitution.project_id == project.id)
            .order_by(ProjectConstitution.version.asc())
        )
        res_const = await db.execute(stmt_const)
        constitutions = [
            {
                "version": c.version,
                "status": c.status,
                "is_approved": c.is_approved,
                "goals": c.goals,
                "requirements": c.requirements,
                "scope": c.scope,
                "ux_specs": c.ux_specs,
                "technical_direction": c.technical_direction,
                "decisions": c.decisions,
                "assumptions": c.assumptions,
                "open_questions": c.open_questions,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in res_const.scalars().all()
        ]

        # 2. Packages
        from promptiq.models.package import PromptPackage

        stmt_pkg = (
            select(PromptPackage)
            .where(PromptPackage.project_id == project.id)
            .order_by(PromptPackage.created_at.asc())
        )
        res_pkg = await db.execute(stmt_pkg)
        packages = [
            {
                "id": p.id,
                "target_environment": p.target_environment,
                "output_type": p.output_type,
                "manifest": p.manifest,
                "files": p.files,
                "warnings": p.warnings,
                "is_validated": p.is_validated,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in res_pkg.scalars().all()
        ]

        # 3. Discovery Sessions
        from promptiq.models.discovery import DiscoverySession

        stmt_disc = (
            select(DiscoverySession)
            .where(DiscoverySession.project_id == project.id)
            .order_by(DiscoverySession.created_at.asc())
        )
        res_disc = await db.execute(stmt_disc)
        discovery_sessions = [
            {
                "id": d.id,
                "task_type": d.task_type,
                "depth": d.depth,
                "current_stage": d.current_stage,
                "is_completed": d.is_completed,
                "initial_intake": d.initial_intake,
                "answers": d.answers,
                "extracted_facts": d.extracted_facts,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in res_disc.scalars().all()
        ]

        # 4. Research Jobs & Evidence Ledger
        from promptiq.models.research import EvidenceClaim, ResearchJob, SourceRecord

        stmt_res = (
            select(ResearchJob)
            .where(ResearchJob.project_id == project.id)
            .order_by(ResearchJob.created_at.asc())
        )
        res_res = await db.execute(stmt_res)
        research_jobs = []
        for rj in res_res.scalars().all():
            stmt_sources = select(SourceRecord).where(SourceRecord.research_job_id == rj.id)
            res_s = await db.execute(stmt_sources)
            sources = [
                {
                    "id": s.id,
                    "url": s.url,
                    "title": s.title,
                    "publisher": s.publisher,
                    "retrieved_at": s.retrieved_at.isoformat() if s.retrieved_at else None,
                }
                for s in res_s.scalars().all()
            ]

            stmt_claims = select(EvidenceClaim).where(EvidenceClaim.research_job_id == rj.id)
            res_c = await db.execute(stmt_claims)
            claims = [
                {
                    "id": c.id,
                    "claim_text": c.claim_text,
                    "support_status": c.support_status,
                    "confidence_score": c.confidence_score,
                    "excerpt": c.excerpt,
                }
                for c in res_c.scalars().all()
            ]

            research_jobs.append(
                {
                    "id": rj.id,
                    "query": rj.query,
                    "mode": rj.mode,
                    "status": rj.status,
                    "summary": rj.summary,
                    "sources": sources,
                    "claims": claims,
                    "created_at": rj.created_at.isoformat() if rj.created_at else None,
                }
            )

        # 5. Checkpoints
        from promptiq.models.memory import Checkpoint

        stmt_chk = (
            select(Checkpoint)
            .where(Checkpoint.project_id == project.id)
            .order_by(Checkpoint.created_at.asc())
        )
        res_chk = await db.execute(stmt_chk)
        checkpoints = [
            {
                "id": chk.id,
                "phase": chk.phase,
                "summary": chk.summary,
                "verified_state": chk.verified_state,
                "blockers": chk.blockers,
                "next_actions": chk.next_actions,
                "created_at": chk.created_at.isoformat() if chk.created_at else None,
            }
            for chk in res_chk.scalars().all()
        ]

        return {
            "schema_version": "1.0.0",
            "project": {
                "id": project.id,
                "workspace_id": project.workspace_id,
                "name": project.name,
                "description": project.description,
                "current_constitution_version": project.current_constitution_version,
                "visibility": project.visibility,
                "created_at": project.created_at.isoformat() if project.created_at else None,
            },
            "constitutions": constitutions,
            "packages": packages,
            "discovery_sessions": discovery_sessions,
            "research_jobs": research_jobs,
            "checkpoints": checkpoints,
            "exported_at": datetime.now(UTC).isoformat(),
        }
