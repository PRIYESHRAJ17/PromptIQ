"""Durable workflow execution and background job service."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import ConflictError, NotFoundError, TenantIsolationError
from promptiq.core.logging import logger
from promptiq.models.job import WorkflowJob


class WorkflowJobService:
    """Manages asynchronous job lifecycle, transitions, lease management, and checkpointing."""

    @staticmethod
    async def create_job(
        db: AsyncSession,
        user_id: str,
        workspace_id: str,
        operation_type: str,
        project_id: str | None = None,
        idempotency_key: str | None = None,
        initial_stage: str = "initialization",
        checkpoint_data: dict[str, Any] | None = None,
    ) -> WorkflowJob:
        """Creates a new durable background workflow job, respecting idempotency keys."""
        if idempotency_key:
            stmt = select(WorkflowJob).where(WorkflowJob.idempotency_key == idempotency_key)
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                if existing.workspace_id != workspace_id:
                    raise TenantIsolationError(
                        message="Idempotency key conflicts across workspaces",
                        details={"idempotency_key": idempotency_key},
                    )
                logger.info(
                    "Returning existing workflow job for idempotency key %s (Job ID: %s)",
                    idempotency_key,
                    existing.id,
                )
                return existing

        job = WorkflowJob(
            user_id=user_id,
            workspace_id=workspace_id,
            project_id=project_id,
            operation_type=operation_type,
            status="QUEUED",
            current_stage=initial_stage,
            stage_history=[
                {
                    "stage": initial_stage,
                    "status": "QUEUED",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ],
            progress_percent=0,
            execution_provenance={},
            checkpoint_data=checkpoint_data or {},
            result_data={},
            idempotency_key=idempotency_key,
            retry_count=0,
            max_retries=3,
        )
        db.add(job)
        await db.flush()
        return job

    @staticmethod
    async def acquire_lease(
        db: AsyncSession,
        job_id: str,
        worker_id: str,
        lease_duration_seconds: int = 60,
    ) -> bool:
        """Atomically acquires lease on a queued or running job."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job or job.status not in ("QUEUED", "RUNNING"):
            return False

        now = datetime.now(UTC)
        lease_exp = job.lease_expires_at
        if lease_exp and lease_exp.tzinfo is None:
            lease_exp = lease_exp.replace(tzinfo=UTC)

        if job.lease_owner and lease_exp and lease_exp > now and job.lease_owner != worker_id:
            return False

        job.lease_owner = worker_id
        job.lease_expires_at = now + timedelta(seconds=lease_duration_seconds)
        job.fencing_token = (getattr(job, "fencing_token", 0) or 0) + 1
        job.status = "RUNNING"
        await db.flush()
        return True

    @staticmethod
    async def update_progress(
        db: AsyncSession,
        job_id: str,
        stage: str,
        progress_percent: int,
        checkpoint: dict[str, Any] | None = None,
        provenance_update: dict[str, Any] | None = None,
        lease_worker_id: str | None = None,
        fencing_token: int | None = None,
    ) -> WorkflowJob:
        """Updates job stage, progress, and checkpoint data while extending lease."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("WorkflowJob", job_id)

        # Fencing token verification to reject stale workers
        if fencing_token is not None and getattr(job, "fencing_token", 0) != fencing_token:
            raise ConflictError(
                expected_version=fencing_token,
                actual_version=getattr(job, "fencing_token", 0),
            )

        now = datetime.now(UTC)
        job.current_stage = stage
        job.progress_percent = max(0, min(100, progress_percent))

        stage_record = {
            "stage": stage,
            "status": "RUNNING",
            "progress_percent": progress_percent,
            "timestamp": now.isoformat(),
        }
        hist = list(job.stage_history or [])
        hist.append(stage_record)
        job.stage_history = hist

        if checkpoint:
            chk = dict(job.checkpoint_data or {})
            chk.update(checkpoint)
            job.checkpoint_data = chk

        if provenance_update:
            prov = dict(job.execution_provenance or {})
            prov.update(provenance_update)
            job.execution_provenance = prov

        if lease_worker_id and job.lease_owner == lease_worker_id:
            job.lease_expires_at = now + timedelta(seconds=60)

        await db.flush()
        return job

    @staticmethod
    async def pause_job(
        db: AsyncSession,
        job_id: str,
        reason: str,
        checkpoint: dict[str, Any] | None = None,
    ) -> WorkflowJob:
        """Transitions job to PAUSED state (e.g. for quota exhaustion or review approval)."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("WorkflowJob", job_id)

        job.status = "PAUSED"
        job.failure_reason = reason
        job.lease_owner = None
        job.lease_expires_at = None

        if checkpoint:
            chk = dict(job.checkpoint_data or {})
            chk.update(checkpoint)
            job.checkpoint_data = chk

        hist = list(job.stage_history or [])
        hist.append(
            {
                "stage": job.current_stage or "paused",
                "status": "PAUSED",
                "reason": reason,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        job.stage_history = hist
        await db.flush()
        return job

    @staticmethod
    async def resume_job(
        db: AsyncSession,
        job_id: str,
        user_id: str,
        workspace_id: str,
    ) -> WorkflowJob:
        """Resumes a paused job from its last recorded checkpoint."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("WorkflowJob", job_id)

        if job.workspace_id != workspace_id:
            raise TenantIsolationError("Cannot resume job from another workspace")

        if job.status not in ("PAUSED", "FAILED"):
            raise ConflictError(
                expected_version=1,
                actual_version=1,
            )

        job.status = "QUEUED"
        job.retry_count += 1
        job.failure_reason = None
        job.lease_owner = None
        job.lease_expires_at = None

        hist = list(job.stage_history or [])
        hist.append(
            {
                "stage": job.current_stage or "resumed",
                "status": "RESUMED",
                "retry_count": job.retry_count,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        job.stage_history = hist
        await db.flush()
        return job

    @staticmethod
    async def cancel_job(
        db: AsyncSession,
        job_id: str,
        user_id: str,
        workspace_id: str,
        reason: str = "Cancelled by user",
    ) -> WorkflowJob:
        """Transitions job to CANCELLED state."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("WorkflowJob", job_id)

        if job.workspace_id != workspace_id:
            raise TenantIsolationError("Cannot cancel job belonging to another workspace")

        job.status = "CANCELLED"
        job.failure_reason = reason
        job.lease_owner = None
        job.lease_expires_at = None
        job.completed_at = datetime.now(UTC)

        hist = list(job.stage_history or [])
        hist.append(
            {
                "stage": job.current_stage or "cancelled",
                "status": "CANCELLED",
                "reason": reason,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        job.stage_history = hist
        await db.flush()
        return job

    @staticmethod
    async def complete_job(
        db: AsyncSession,
        job_id: str,
        result_data: dict[str, Any],
        has_warnings: bool = False,
        fencing_token: int | None = None,
    ) -> WorkflowJob:
        """Marks a job as completed or completed with warnings."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("WorkflowJob", job_id)

        # Fencing token verification to reject stale workers
        if fencing_token is not None and getattr(job, "fencing_token", 0) != fencing_token:
            raise ConflictError(
                expected_version=fencing_token,
                actual_version=getattr(job, "fencing_token", 0),
            )

        job.status = "COMPLETED_WITH_WARNINGS" if has_warnings else "COMPLETED"
        job.progress_percent = 100
        job.result_data = result_data
        job.lease_owner = None
        job.lease_expires_at = None
        job.completed_at = datetime.now(UTC)

        hist = list(job.stage_history or [])
        hist.append(
            {
                "stage": job.current_stage or "completed",
                "status": job.status,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        job.stage_history = hist
        await db.flush()
        return job

    @staticmethod
    async def fail_job(
        db: AsyncSession,
        job_id: str,
        error_message: str,
    ) -> WorkflowJob:
        """Marks a job as failed, or transitions to DEAD_LETTER if retries exhausted."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("WorkflowJob", job_id)

        job.failure_reason = error_message
        job.lease_owner = None
        job.lease_expires_at = None

        if job.retry_count < job.max_retries:
            job.status = "QUEUED"
            job.retry_count += 1
            hist_status = f"RETRY_{job.retry_count}"
        else:
            job.status = "FAILED"
            job.completed_at = datetime.now(UTC)
            hist_status = "DEAD_LETTER"

        hist = list(job.stage_history or [])
        hist.append(
            {
                "stage": job.current_stage or "failure",
                "status": hist_status,
                "error": error_message,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        job.stage_history = hist
        await db.flush()
        return job

    @staticmethod
    async def recover_stale_jobs(
        db: AsyncSession,
        timeout_seconds: int = 300,
    ) -> int:
        """Recovers jobs abandoned by crashed workers (expired leases) back to QUEUED."""
        cutoff = datetime.now(UTC)
        stmt = select(WorkflowJob).where(
            WorkflowJob.status == "RUNNING",
            WorkflowJob.lease_expires_at < cutoff,
        )
        res = await db.execute(stmt)
        stale_jobs = res.scalars().all()
        recovered_count = 0
        for job in stale_jobs:
            job.status = "QUEUED"
            job.lease_owner = None
            job.lease_expires_at = None
            hist = list(job.stage_history or [])
            hist.append(
                {
                    "stage": job.current_stage or "stale_recovery",
                    "status": "LEASE_EXPIRED_REQUEUED",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            job.stage_history = hist
            recovered_count += 1

        if recovered_count > 0:
            await db.flush()
            logger.info("Recovered %d stale workflow jobs", recovered_count)
        return recovered_count

    @staticmethod
    async def get_job(
        db: AsyncSession,
        job_id: str,
        workspace_id: str,
    ) -> WorkflowJob:
        """Retrieves a single job with workspace isolation enforcement."""
        stmt = select(WorkflowJob).where(WorkflowJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("WorkflowJob", job_id)
        if job.workspace_id != workspace_id:
            raise TenantIsolationError("Job belongs to another workspace")
        return job

    @staticmethod
    async def list_jobs(
        db: AsyncSession,
        workspace_id: str,
        project_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WorkflowJob]:
        """Lists jobs within a workspace with optional filters and pagination."""
        stmt = select(WorkflowJob).where(WorkflowJob.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(WorkflowJob.project_id == project_id)
        if status:
            stmt = stmt.where(WorkflowJob.status == status)

        stmt = (
            stmt.order_by(desc(WorkflowJob.created_at))
            .limit(min(100, max(1, limit)))
            .offset(max(0, offset))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def execute_agent_workflow_job(
        db: AsyncSession,
        job_id: str,
        worker_id: str,
    ) -> WorkflowJob:
        """Executes an agent workflow job through the AutonomousAgentLoop runtime."""
        from promptiq.orchestrator.agent_loop import AutonomousAgentLoop

        job, fencing_token = await WorkflowJobService.claim_job(db, job_id, worker_id)
        if not job:
            raise ConflictError(expected_version=1, actual_version=0)

        agent = AutonomousAgentLoop()
        task_objective = (job.checkpoint_data or {}).get(
            "objective", f"Execute background task for job {job_id}"
        )
        task_type = (job.checkpoint_data or {}).get("task_type", "software_engineering")

        try:
            summary = await agent.run(
                objective=task_objective,
                task_name=f"Job-{job_id[:8]}",
                task_type=task_type,
            )
            completed_job = await WorkflowJobService.complete_job(
                db=db,
                job_id=job_id,
                result_data={
                    "status": summary.status,
                    "plan_id": summary.plan_id,
                    "total_iterations": summary.total_iterations,
                    "replan_count": summary.replan_count,
                    "deliverable": summary.deliverable,
                },
                has_warnings=summary.status != "completed",
                fencing_token=fencing_token,
            )
            return completed_job
        except Exception as exc:
            logger.exception("Agent workflow job %s failed: %s", job_id, exc)
            return await WorkflowJobService.fail_job(db, job_id, str(exc))
