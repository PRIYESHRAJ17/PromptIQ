"""Adaptive Discovery and intake API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.exceptions import NotFoundError, TenantIsolationError
from promptiq.discovery.adaptive import AdaptiveDiscoveryEngine
from promptiq.models.user import User
from promptiq.schemas.discovery import (
    DiscoveryAnswerSubmit,
    DiscoverySessionResponse,
    InitialIntakeRequest,
)

router = APIRouter(prefix="/projects/{project_id}/discovery", tags=["Discovery"])


@router.post("/start", response_model=DiscoverySessionResponse, status_code=status.HTTP_201_CREATED)
async def start_discovery(
    project_id: str,
    intake: InitialIntakeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start an adaptive discovery session from the foundational 4-input intake."""
    try:
        session_resp = await AdaptiveDiscoveryEngine.start_session(db, project_id, user.id, intake)
        return session_resp
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/sessions/{session_id}/answers", response_model=DiscoverySessionResponse)
async def submit_discovery_answers(
    project_id: str,
    session_id: str,
    answers_in: DiscoveryAnswerSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit answers to discovery questions, updating requirements and calculating next steps."""
    try:
        session_resp = await AdaptiveDiscoveryEngine.submit_answers(
            db, session_id, user.id, answers_in.answers
        )
        return session_resp
    except (NotFoundError, TenantIsolationError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
