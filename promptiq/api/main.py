"""Main FastAPI Application Entrypoint for PromptIQ."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from promptiq import __version__
from promptiq.api.routes import (
    auth_router,
    compiler_router,
    constitution_router,
    critic_router,
    discovery_router,
    eval_router,
    governor_router,
    memory_router,
    projects_router,
    registries_router,
    research_router,
    telegram_router,
)
from promptiq.core.database import close_db, init_db
from promptiq.core.exceptions import PromptIQException
from promptiq.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle manager."""
    logger.info("PromptIQ Backend starting up...")
    await init_db()
    logger.info("PromptIQ Backend ready to serve requests.")
    yield
    logger.info("PromptIQ Backend shutting down...")
    await close_db()


app = FastAPI(
    title="PromptIQ API",
    version=__version__,
    description=(
        "Universal Prompt Intelligence, Project Engineering, and Cross-Agent Continuity Platform.\n\n"
        "**Strict Invariants**:\n"
        "- Zero-price to end-users (₹0)\n"
        "- Strictly No BYOK / No user API keys\n"
        "- No local inference required\n"
        "- Canonical versioned Project Constitution\n"
        "- Website frontend strictly out of scope\n"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(PromptIQException)
async def promptiq_exception_handler(request: Request, exc: PromptIQException):
    """Custom exception handler for all domain-specific PromptIQ exceptions."""
    logger.warning(
        f"Domain exception: {exc.error_code} - {exc.message}",
        extra={"error_code": exc.error_code, "details": exc.details, "path": request.url.path},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container probes and operational monitoring."""
    return {
        "status": "healthy",
        "version": __version__,
        "zero_price_policy": "enforced",
        "byok_prohibited": True,
    }


# Mount API v1 Routers
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(projects_router, prefix=api_v1_prefix)
app.include_router(discovery_router, prefix=api_v1_prefix)
app.include_router(constitution_router, prefix=api_v1_prefix)
app.include_router(compiler_router, prefix=api_v1_prefix)
app.include_router(critic_router, prefix=api_v1_prefix)
app.include_router(research_router, prefix=api_v1_prefix)
app.include_router(registries_router, prefix=api_v1_prefix)
app.include_router(eval_router, prefix=api_v1_prefix)
app.include_router(memory_router, prefix=api_v1_prefix)
app.include_router(governor_router, prefix=api_v1_prefix)
app.include_router(telegram_router, prefix=api_v1_prefix)
