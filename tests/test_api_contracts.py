"""Test API Contracts, OpenAPI specifications, and frontend exclusion invariant."""

import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Verifies that the /health endpoint is operational and reflects project invariants."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["zero_price_policy"] == "enforced"
    assert data["byok_prohibited"] is True


@pytest.mark.asyncio
async def test_openapi_contract_schema(client: AsyncClient):
    """Verifies that OpenAPI documentation is fully generated and covers core domains."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    assert schema["openapi"].startswith("3.")
    assert "PromptIQ API" in schema["info"]["title"]

    paths = schema["paths"]
    # Verify core API domain coverage
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/projects" in paths
    assert "/api/v1/projects/{project_id}/constitution" in paths
    assert "/api/v1/projects/{project_id}/compile" in paths
    assert "/api/v1/critic/autopsy" in paths
    assert "/api/v1/projects/{project_id}/research" in paths
    assert "/api/v1/registries/models" in paths
    assert "/api/v1/registries/environments" in paths
    assert "/api/v1/projects/{project_id}/eval/run" in paths
    assert "/api/v1/projects/{project_id}/memory/checkpoints" in paths
    assert "/api/v1/status/capacity" in paths
    assert "/api/v1/telegram/webhook" in paths


@pytest.mark.asyncio
async def test_strictly_no_website_frontend_invariant():
    """
    SECTION 0 Invariant Assertion:
    The website frontend is strictly out of scope.
    Verify that no React/Next.js/HTML pages, CSS files, or frontend shells exist in the repository.
    """
    prohibited_extensions = {".jsx", ".tsx", ".vue", ".svelte", ".css", ".scss", ".sass"}
    prohibited_dirs = {"pages", "components", "app", "ui", "styles", "public"}

    for root, dirs, files in os.walk("."):
        # Ignore virtualenv, git, and storage
        if ".venv" in root or ".git" in root or "storage" in root:
            continue

        for d in dirs:
            # Check for top-level frontend directories
            if root == "." and d.lower() in prohibited_dirs:
                pytest.fail(f"Prohibited frontend directory detected: {d}")

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in prohibited_extensions:
                pytest.fail(f"Prohibited frontend file detected: {os.path.join(root, f)}")
