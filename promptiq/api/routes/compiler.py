"""Target Compilation and Package export API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.compiler.target_compiler import target_compiler
from promptiq.core.exceptions import (
    ConstitutionApprovalRequiredError,
    NotFoundError,
    TenantIsolationError,
)
from promptiq.models.user import User
from promptiq.schemas.package import (
    PackageCompileRequest,
    PackageExportResponse,
    PromptPackageResponse,
)
from promptiq.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}", tags=["Compiler"])


@router.post("/compile", response_model=PromptPackageResponse, status_code=status.HTTP_201_CREATED)
async def compile_target_package(
    project_id: str,
    compile_req: PackageCompileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compile the approved Project Constitution into a target-native instruction package."""
    try:
        package_resp = await target_compiler.compile_package(
            db,
            project_id=project_id,
            user_id=user.id,
            target_environment=compile_req.target_environment,
            output_type=compile_req.output_type,
            surface="api",
        )
        return package_resp
    except ConstitutionApprovalRequiredError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e.message)
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/packages/{package_id}/export", response_model=PackageExportResponse)
async def export_package(
    project_id: str,
    package_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export complete target package bundle with manifest and files."""
    from sqlalchemy import select

    from promptiq.models.package import PromptPackage

    # Enforce tenant isolation
    try:
        await ProjectService.get_project(db, project_id, user.id)
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    stmt = select(PromptPackage).where(PromptPackage.id == package_id, PromptPackage.project_id == project_id)
    res = await db.execute(stmt)
    pkg = res.scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    return PackageExportResponse(
        package_id=pkg.id,
        target_environment=pkg.target_environment,
        file_count=len(pkg.files),
        manifest=pkg.manifest,
        files=pkg.files,
    )
