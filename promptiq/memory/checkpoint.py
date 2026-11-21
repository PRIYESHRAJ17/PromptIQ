"""Milestone Checkpointing and cross-agent state persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.models.audit import AuditEvent
from promptiq.models.memory import Checkpoint
from promptiq.schemas.memory import CheckpointCreate, CheckpointResponse
from promptiq.services.project_service import ProjectService


class CheckpointManager:
    """Creates, retrieves, and validates milestone checkpoints for cross-surface handoffs."""

    @classmethod
    async def create_checkpoint(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        checkpoint_in: CheckpointCreate,
        surface: str = "api",
    ) -> CheckpointResponse:
        """Records a verified snapshot of project state, open blockers, and next steps."""
        project = await ProjectService.get_project(db, project_id, user_id)

        checkpoint = Checkpoint(
            project_id=project.id,
            phase=checkpoint_in.phase,
            summary=checkpoint_in.summary,
            verified_state=checkpoint_in.verified_state,
            blockers=checkpoint_in.blockers,
            next_actions=checkpoint_in.next_actions,
            files_snapshot={},
        )
        db.add(checkpoint)

        # Audit log
        audit = AuditEvent(
            workspace_id=project.workspace_id,
            project_id=project.id,
            user_id=user_id,
            action="checkpoint.created",
            surface=surface,
            payload={"phase": checkpoint_in.phase, "summary": checkpoint_in.summary},
        )
        db.add(audit)
        await db.flush()

        return CheckpointResponse.model_validate(checkpoint)

    @classmethod
    async def list_checkpoints(
        cls, db: AsyncSession, project_id: str, user_id: str
    ) -> list[CheckpointResponse]:
        """Lists all recorded checkpoints for a project in reverse chronological order."""
        await ProjectService.get_project(db, project_id, user_id)

        stmt = (
            select(Checkpoint)
            .where(Checkpoint.project_id == project_id)
            .order_by(Checkpoint.created_at.desc())
        )
        res = await db.execute(stmt)
        checkpoints = res.scalars().all()
        return [CheckpointResponse.model_validate(cp) for cp in checkpoints]
