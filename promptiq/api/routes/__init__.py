"""API Routes module."""

from promptiq.api.routes.auth import router as auth_router
from promptiq.api.routes.compiler import router as compiler_router
from promptiq.api.routes.constitution import router as constitution_router
from promptiq.api.routes.critic import router as critic_router
from promptiq.api.routes.discovery import router as discovery_router
from promptiq.api.routes.eval import router as eval_router, system_eval_router
from promptiq.api.routes.governor import router as governor_router
from promptiq.api.routes.jobs import router as jobs_router
from promptiq.api.routes.memory import router as memory_router
from promptiq.api.routes.projects import router as projects_router
from promptiq.api.routes.registries import router as registries_router
from promptiq.api.routes.research import router as research_router
from promptiq.api.routes.telegram import router as telegram_router
from promptiq.mcp.remote import router as mcp_router

__all__ = [
    "auth_router",
    "projects_router",
    "discovery_router",
    "constitution_router",
    "compiler_router",
    "critic_router",
    "research_router",
    "registries_router",
    "eval_router",
    "system_eval_router",
    "memory_router",
    "governor_router",
    "jobs_router",
    "telegram_router",
    "mcp_router",
]
