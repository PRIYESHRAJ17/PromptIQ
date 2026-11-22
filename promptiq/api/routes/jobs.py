"""Workflow and background job API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.models.user import User
from promptiq.schemas.job import JobCancelRequest, JobCreate, JobResponse
from promptiq.services.job_service import WorkflowJobService
from promptiq.services.project_service import ProjectService

router = APIRouter(prefix="/jobs", tags=["Workflow Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_job(
    job_in: JobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiates a durable asynchronous workflow job."""
    # Resolve user's active workspace
    workspace = await ProjectService.get_user_default_workspace(db, user.id)

    job = await WorkflowJobService.create_job(
        db=db,
        user_id=user.id,
        workspace_id=workspace.workspace_id,
        operation_type=job_in.operation_type,
        project_id=job_in.project_id,
        idempotency_key=job_in.idempotency_key,
        initial_stage=job_in.initial_stage,
        checkpoint_data=job_in.checkpoint_data,
    )
    return JobResponse.model_validate(job)


@router.get("", response_model=list[JobResponse])
async def list_workflow_jobs(
    project_id: str | None = Query(default=None, description="Filter by project ID"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists workflow jobs within the authenticated user's workspace."""
    workspace = await ProjectService.get_user_default_workspace(db, user.id)
    jobs = await WorkflowJobService.list_jobs(
        db=db,
        workspace_id=workspace.workspace_id,
        project_id=project_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [JobResponse.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_workflow_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full status, checkpoint, and history of a workflow job."""
    workspace = await ProjectService.get_user_default_workspace(db, user.id)
    job = await WorkflowJobService.get_job(db=db, job_id=job_id, workspace_id=workspace.workspace_id)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_workflow_job(
    job_id: str,
    req: JobCancelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancels a pending or running workflow job."""
    workspace = await ProjectService.get_user_default_workspace(db, user.id)
    job = await WorkflowJobService.cancel_job(
        db=db,
        job_id=job_id,
        user_id=user.id,
        workspace_id=workspace.workspace_id,
        reason=req.reason,
    )
    return JobResponse.model_validate(job)


@router.post("/{job_id}/resume", response_model=JobResponse)
async def resume_workflow_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resumes a paused workflow job from its latest saved checkpoint."""
    workspace = await ProjectService.get_user_default_workspace(db, user.id)
    job = await WorkflowJobService.resume_job(
        db=db,
        job_id=job_id,
        user_id=user.id,
        workspace_id=workspace.workspace_id,
    )
    return JobResponse.model_validate(job)
