"""Live Web Search Connector querying public documentation endpoints."""

import urllib.parse
from typing import Any

import httpx

from promptiq.core.logging import logger
from promptiq.research.connectors.base import BaseSearchConnector, MockSearchConnector


class LiveWebSearchConnector(BaseSearchConnector):
    """Retrieves live web knowledge from public endpoints with fallback to deterministic mock.

    Requires NO API keys (100% free public endpoints), preserving PromptIQ's zero-cost invariant.
    """

    def __init__(self, fallback_on_error: bool = True):
        self.fallback = MockSearchConnector() if fallback_on_error else None

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Queries public REST knowledge sources (e.g. Wikipedia OpenSearch / API) for live evidence."""
        results: list[dict[str, Any]] = []

        try:
            encoded_query = urllib.parse.quote(query)
            wiki_api_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={encoded_query}&utf8=&format=json&srlimit={max_results}"
            )

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    wiki_api_url,
                    headers={"User-Agent": "PromptIQ-ResearchEngine/1.0 (academic; open-source)"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    search_items = data.get("query", {}).get("search", [])
                    for item in search_items[:max_results]:
                        title = item.get("title", "")
                        clean_snippet = (
                            item.get("snippet", "")
                            .replace('<span class="searchmatch">', "")
                            .replace("</span>", "")
                        )
                        page_slug = urllib.parse.quote(title.replace(" ", "_"))
                        results.append(
                            {
                                "url": f"https://en.wikipedia.org/wiki/{page_slug}",
                                "title": title,
                                "publisher": "Wikimedia / Wikipedia Foundation",
                                "source_type": "independent_encyclopedia",
                                "publication_date": item.get("timestamp", "")[:10] or "2024-01-01",
                                "content": clean_snippet or f"Summary of {title}",
                                "locator": f"Page: {title}",
                            }
                        )

            if results:
                logger.info(f"Live search retrieved {len(results)} authoritative sources for query '{query}'")
                return results

        except Exception as e:
            logger.warning(f"Live search query failed or timed out: {e}. Falling back to deterministic knowledge base.")

        # Fallback to mock connector if live query yielded no results or network is offline
        if self.fallback:
            return await self.fallback.search(query, max_results=max_results)

        return []
