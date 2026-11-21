"""Research Intelligence and Evidence Ledger API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.exceptions import NotFoundError, TenantIsolationError
from promptiq.models.user import User
from promptiq.research.engine import research_engine
from promptiq.schemas.research import ResearchRequest, ResearchResponse

router = APIRouter(prefix="/projects/{project_id}/research", tags=["Research"])


@router.post("", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
async def execute_research(
    project_id: str,
    research_req: ResearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute deep or quick research and record verified claims in the Evidence Ledger."""
    try:
        res = await research_engine.execute_research(db, project_id, user.id, research_req)
        return res
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
