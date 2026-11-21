"""Model and Environment Registry API routes."""

from fastapi import APIRouter, HTTPException, Query, status

from promptiq.registry.env_registry import EnvironmentRegistryService
from promptiq.registry.model_registry import ModelRegistryService
from promptiq.schemas.registry import EnvironmentRecordSchema, ModelRecordSchema

router = APIRouter(prefix="/registries", tags=["Registries"])


@router.get("/models", response_model=list[ModelRecordSchema])
async def list_models(zero_price_only: bool = Query(default=False)):
    """List supported models with documented capabilities and verified pricing tier."""
    return ModelRegistryService.list_models(zero_price_only=zero_price_only)


@router.get("/models/{model_id}", response_model=ModelRecordSchema)
async def get_model(model_id: str):
    """Get verified capabilities and rate limits for a specific model."""
    model = ModelRegistryService.get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model '{model_id}' not found")
    return model


@router.get("/environments", response_model=list[EnvironmentRecordSchema])
async def list_environments():
    """List supported host environments (Antigravity, Claude Code, Cursor, Codex, Gemini CLI)."""
    return EnvironmentRegistryService.list_environments()


@router.get("/environments/{host}", response_model=EnvironmentRecordSchema)
async def get_environment(host: str):
    """Get host capabilities and manifest rules for a specific execution surface."""
    env = EnvironmentRegistryService.get_environment(host)
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Environment '{host}' not found")
    return env
