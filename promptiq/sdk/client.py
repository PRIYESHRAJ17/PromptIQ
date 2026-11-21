"""PromptIQ Python Client SDK."""

from typing import Any

import httpx


class PromptIQClient:
    """Programmatic Python SDK client for the PromptIQ API."""

    def __init__(self, base_url: str = "http://localhost:8000", token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def register(self, email: str, password: str, full_name: str | None = None) -> dict[str, Any]:
        resp = await self._client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        resp.raise_for_status()
        return resp.json()

    async def login(self, email: str, password: str) -> dict[str, Any]:
        resp = await self._client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        return data

    async def create_project(self, name: str, description: str | None = None) -> dict[str, Any]:
        resp = await self._client.post(
            "/api/v1/projects",
            json={"name": name, "description": description},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def list_projects(self) -> list[dict[str, Any]]:
        resp = await self._client.get("/api/v1/projects", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    async def get_constitution(self, project_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/api/v1/projects/{project_id}/constitution", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    async def approve_constitution(self, project_id: str, approve: bool = True) -> dict[str, Any]:
        resp = await self._client.post(
            f"/api/v1/projects/{project_id}/constitution/approve",
            json={"approve": approve},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def compile_package(
        self,
        project_id: str,
        target_environment: str = "google-antigravity",
        output_type: str = "complete_package",
    ) -> dict[str, Any]:
        resp = await self._client.post(
            f"/api/v1/projects/{project_id}/compile",
            json={"target_environment": target_environment, "output_type": output_type},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def review_prompt(self, prompt_text: str, target: str = "google-antigravity") -> dict[str, Any]:
        resp = await self._client.post(
            "/api/v1/critic/autopsy",
            json={"prompt_text": prompt_text, "target_environment": target},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def research(self, project_id: str, query: str, mode: str = "quick") -> dict[str, Any]:
        resp = await self._client.post(
            f"/api/v1/projects/{project_id}/research",
            json={"query": query, "mode": mode},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()
