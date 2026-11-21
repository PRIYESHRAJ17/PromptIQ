"""Project management and tenant isolation service."""

from sqlalchemy import select
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
    async def verify_workspace_access(db: AsyncSession, user_id: str, workspace_id: str) -> WorkspaceMembership:
        """Verifies that the user has valid membership in the specified workspace."""
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.workspace_id == workspace_id,
        )
        res = await db.execute(stmt)
        membership = res.scalar_one_or_none()
        if not membership:
            raise TenantIsolationError(f"User '{user_id}' does not have access to workspace '{workspace_id}'")
        return membership

    @classmethod
    async def create_project(cls, db: AsyncSession, user_id: str, project_in: ProjectCreate, surface: str = "api") -> Project:
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
    async def list_projects(cls, db: AsyncSession, user_id: str, workspace_id: str | None = None) -> list[Project]:
        """Lists all projects in the workspace accessible to the user."""
        if workspace_id:
            await cls.verify_workspace_access(db, user_id, workspace_id)
            stmt = select(Project).where(Project.workspace_id == workspace_id).order_by(Project.created_at.desc())
        else:
            # Query all workspaces the user belongs to
            ws_stmt = select(WorkspaceMembership.workspace_id).where(WorkspaceMembership.user_id == user_id)
            res_ws = await db.execute(ws_stmt)
            allowed_ws_ids = res_ws.scalars().all()
            stmt = select(Project).where(Project.workspace_id.in_(allowed_ws_ids)).order_by(Project.created_at.desc())

        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def delete_project(cls, db: AsyncSession, project_id: str, user_id: str, surface: str = "api") -> bool:
        """Deletes a project after validating tenant boundaries."""
        project = await cls.get_project(db, project_id, user_id)
        workspace_id = project.workspace_id

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
