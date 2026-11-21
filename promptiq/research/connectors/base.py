"""Search and retrieval connectors for research."""

from abc import ABC, abstractmethod
from typing import Any


class BaseSearchConnector(ABC):
    """Abstract interface for public document retrieval."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Executes search and returns a list of candidate source records."""
        pass


class MockSearchConnector(BaseSearchConnector):
    """Deterministic search connector for reproducible testing."""

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        return [
            {
                "url": "https://modelcontextprotocol.io/specification/2024-11-05",
                "title": "Model Context Protocol Specification v1.0",
                "publisher": "Anthropic / Model Context Protocol Working Group",
                "source_type": "standard",
                "publication_date": "2024-11-05",
                "content": "The Model Context Protocol (MCP) standardizes how clients provide context to LLMs, exposing tools, resources, and prompt templates over JSON-RPC.",
                "locator": "Section 2.1 Protocol Lifecycle",
            },
            {
                "url": "https://ai.google.dev/gemini-api/docs/models/gemini-v2",
                "title": "Gemini 2.0 Flash Model Reference & Pricing",
                "publisher": "Google AI for Developers",
                "source_type": "official_docs",
                "publication_date": "2024-12-11",
                "content": "Gemini 2.0 Flash is multimodal with a 1,048,576 token context window and structured JSON output mode. Free tier access is provided with 15 RPM.",
                "locator": "Pricing & Quotas",
            },
        ][:max_results]
