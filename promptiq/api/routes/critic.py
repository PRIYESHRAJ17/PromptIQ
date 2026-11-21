"""Prompt Autopsy and Adversarial Critique API routes."""

from fastapi import APIRouter, Depends

from promptiq.api.deps import get_current_user
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.models.user import User
from promptiq.schemas.critic import AutopsyRequest, AutopsyResponse

router = APIRouter(prefix="/critic", tags=["Prompt Autopsy"])


@router.post("/autopsy", response_model=AutopsyResponse)
async def diagnose_prompt(
    request: AutopsyRequest,
    user: User = Depends(get_current_user),
):
    """Execute adversarial prompt autopsy and diagnostic critique."""
    response = await PromptAutopsyEngine.diagnose_prompt(request, user_id=user.id)
    return response
