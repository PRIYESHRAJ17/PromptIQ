"""Project Memory, Checkpoints, and Context Continuity API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.exceptions import NotFoundError, TenantIsolationError
from promptiq.memory.checkpoint import CheckpointManager
from promptiq.memory.context_compiler import ContextCompiler
from promptiq.models.user import User
from promptiq.schemas.memory import (
    CheckpointCreate,
    CheckpointResponse,
    ContextPackRequest,
    ContextPackResponse,
)

router = APIRouter(prefix="/projects/{project_id}/memory", tags=["Project Memory"])


@router.post("/checkpoints", response_model=CheckpointResponse, status_code=status.HTTP_201_CREATED)
async def create_checkpoint(
    project_id: str,
    checkpoint_in: CheckpointCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a verified milestone checkpoint for cross-session and cross-agent continuity."""
    try:
        cp = await CheckpointManager.create_checkpoint(
            db, project_id, user.id, checkpoint_in, surface="api"
        )
        return cp
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/checkpoints", response_model=list[CheckpointResponse])
async def list_checkpoints(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recorded checkpoints for a project."""
    try:
        return await CheckpointManager.list_checkpoints(db, project_id, user.id)
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/context-pack", response_model=ContextPackResponse)
async def compile_context_pack(
    project_id: str,
    request: ContextPackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compile and pack project context for an external agent within a specified token budget."""
    try:
        return await ContextCompiler.compile_context(db, project_id, user.id, request)
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
