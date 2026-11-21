"""Prompt Test Lab and Benchmark evaluation API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.exceptions import NotFoundError, TenantIsolationError
from promptiq.eval.test_lab import PromptTestLab
from promptiq.models.user import User
from promptiq.schemas.eval import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationSuiteCreate,
)

router = APIRouter(prefix="/projects/{project_id}/eval", tags=["Evaluation Lab"])


@router.post("/suites", status_code=status.HTTP_201_CREATED)
async def create_evaluation_suite(
    project_id: str,
    suite_in: EvaluationSuiteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new evaluation test suite with assertions and edge cases."""
    try:
        suite = await PromptTestLab.create_suite(db, project_id, user.id, suite_in)
        return {"suite_id": suite.id, "name": suite.name, "case_count": len(suite.test_cases)}
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/run", response_model=EvaluationRunResponse)
async def run_evaluation(
    project_id: str,
    run_req: EvaluationRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run an authorized evaluation against a compiled package using fixed assertions."""
    try:
        run_resp = await PromptTestLab.run_evaluation(db, project_id, user.id, run_req)
        return run_resp
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
