"""Project Constitution management API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.exceptions import NotFoundError, TenantIsolationError
from promptiq.models.user import User
from promptiq.schemas.constitution import (
    ConstitutionApprovalRequest,
    ConstitutionResponse,
    ConstitutionUpdate,
)
from promptiq.services.constitution_service import ConstitutionService

router = APIRouter(prefix="/projects/{project_id}/constitution", tags=["Project Constitution"])


@router.get("", response_model=ConstitutionResponse)
async def get_current_constitution(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the active Project Constitution for a project."""
    try:
        constitution = await ConstitutionService.get_current_constitution(db, project_id, user.id)
        return ConstitutionResponse.model_validate(constitution)
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/versions/{version}", response_model=dict)
async def get_constitution_version(
    project_id: str,
    version: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve an immutable historical snapshot of a specific constitution version."""
    try:
        ver_record = await ConstitutionService.get_constitution_by_version(db, project_id, version, user.id)
        return {
            "version": ver_record.version,
            "snapshot": ver_record.snapshot,
            "diff": ver_record.diff,
            "created_at": ver_record.created_at,
        }
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("", response_model=ConstitutionResponse)
async def update_constitution(
    project_id: str,
    update_in: ConstitutionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update requirements or specifications, generating a new immutable Constitution version."""
    try:
        new_const = await ConstitutionService.update_constitution(db, project_id, user.id, update_in, surface="api")
        return ConstitutionResponse.model_validate(new_const)
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/approve", response_model=ConstitutionResponse)
async def approve_constitution(
    project_id: str,
    approval_in: ConstitutionApprovalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User review gate: approve or reject the active Constitution before compilation."""
    try:
        approved_const = await ConstitutionService.approve_constitution(db, project_id, user.id, approval_in, surface="api")
        return ConstitutionResponse.model_validate(approved_const)
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
