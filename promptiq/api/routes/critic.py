"""Prompt Autopsy and Adversarial Critique API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.exceptions import NotFoundError, TenantIsolationError
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.models.user import User
from promptiq.schemas.critic import AutopsyRequest, AutopsyResponse

router = APIRouter(prefix="/critic", tags=["Prompt Autopsy"])


@router.post("/autopsy", response_model=AutopsyResponse)
async def diagnose_prompt(
    request: AutopsyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute adversarial prompt autopsy and diagnostic critique."""
    try:
        response = await PromptAutopsyEngine.diagnose_prompt(request, user_id=user.id, db=db)
        return response
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
