"""Main FastAPI Application Entrypoint for PromptIQ."""

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
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
    jobs_router,
    mcp_router,
    memory_router,
    projects_router,
    registries_router,
    research_router,
    telegram_router,
)
from promptiq.core.config import settings
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

# CORS Configuration - Explicit authorized origins (prevents credential leakage / CSRF)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(PromptIQException)
async def promptiq_exception_handler(request: Request, exc: PromptIQException):
    """Custom exception handler for all domain-specific PromptIQ exceptions."""
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    logger.warning(
        f"Domain exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "request_id": req_id,
        },
    )
    headers = {"X-Request-ID": req_id}
    if hasattr(exc, "retry_after"):
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": req_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic/FastAPI request validation errors into standard PromptIQ error schema."""
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    # Sanitize errors to string-safe serialization
    safe_errors = []
    for err in exc.errors():
        safe_err = dict(err)
        if "input" in safe_err and not isinstance(
            safe_err["input"], (str, int, float, bool, list, dict, type(None))
        ):
            safe_err["input"] = str(safe_err["input"])
        safe_errors.append(safe_err)

    return JSONResponse(
        status_code=422,
        headers={"X-Request-ID": req_id},
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request parameter or body validation failed",
                "details": {"errors": safe_errors},
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": req_id,
            }
        },
    )


# Health & Readiness endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe for container lifecycle monitoring."""
    return {
        "status": "healthy",
        "version": __version__,
        "zero_price_policy": "enforced",
        "byok_prohibited": True,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe for cloud load balancers and orchestrators."""
    from sqlalchemy import text

    from promptiq.core.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})


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
app.include_router(jobs_router, prefix=api_v1_prefix)
app.include_router(governor_router, prefix=api_v1_prefix)
app.include_router(telegram_router, prefix=api_v1_prefix)
app.include_router(mcp_router, prefix=api_v1_prefix)
