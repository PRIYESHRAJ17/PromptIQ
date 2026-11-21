# Multi-stage production Dockerfile for PromptIQ Cloud Backend
# Implements non-root security, zero-price invariant, and portable pure-Python execution

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md /build/
COPY promptiq/ /build/promptiq/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ============================================================
# Final Production Runtime Stage
# ============================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Ensure security: create dedicated non-root service user
RUN groupadd -g 10001 promptiq && \
    useradd -u 10001 -g promptiq -s /bin/bash -m promptiq

# Copy pre-built virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set runtime configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISABLE_SQLALCHEMY_CEXT=1 \
    PROMPTIQ_ENV=production \
    PROMPTIQ_API_HOST=0.0.0.0 \
    PROMPTIQ_API_PORT=8000

# Copy application source code and migrations
COPY --chown=promptiq:promptiq alembic.ini /app/
COPY --chown=promptiq:promptiq alembic/ /app/alembic/
COPY --chown=promptiq:promptiq promptiq/ /app/promptiq/
COPY --chown=promptiq:promptiq data/ /app/data/

# Switch to non-root user
USER promptiq

EXPOSE 8000

# Health check probe for Cloud Run / Kubernetes container liveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

# Start Uvicorn ASGI server (1 worker per container instance preserves SSE memory and rate limiting)
CMD ["uvicorn", "promptiq.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
