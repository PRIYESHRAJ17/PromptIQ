"""Live Web Search Connector querying public documentation endpoints with SSRF transport pinning and injection sanitization."""

import hashlib
import re
import urllib.parse
from typing import Any

from promptiq.core.logging import logger
from promptiq.core.security import safe_fetch_url, validate_and_sanitize_url
from promptiq.research.connectors.base import BaseSearchConnector, MockSearchConnector

# Untrusted input injection sanitization patterns
INJECTION_PATTERNS = re.compile(
    r"\b(ignore\s+(?:all\s+)?previous\s+instructions|system\s+prompt\s+override|<\|im_start\|>|<\|im_end\|>|\[system\]|\[assistant\])\b",
    re.IGNORECASE,
)


def sanitize_untrusted_search_content(text: str) -> str:
    """Neutralizes prompt injection sequences and malformed markup in scraped search excerpts."""
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", " ", text)
    # Neutralize injection patterns
    sanitized = INJECTION_PATTERNS.sub("[REDACTED_INJECTION_PATTERN]", clean)
    # Normalize excessive whitespace
    return re.sub(r"\s+", " ", sanitized).strip()


class LiveWebSearchConnector(BaseSearchConnector):
    """Retrieves live web knowledge from public endpoints with fallback to deterministic mock.

    Requires NO API keys (100% free public endpoints), preserving PromptIQ's zero-cost invariant.
    Enforces transport-level socket pinning via safe_fetch_url and SSRFSafeAsyncTransport.
    """

    def __init__(self, fallback_on_error: bool = True):
        self.fallback = MockSearchConnector() if fallback_on_error else None

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Queries public REST knowledge sources for live evidence with verified socket pinning."""
        results: list[dict[str, Any]] = []

        try:
            encoded_query = urllib.parse.quote(query)
            wiki_api_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={encoded_query}&utf8=&format=json&srlimit={max_results}"
            )

            # Strict SSRF validation and socket-pinned fetch
            resp = await safe_fetch_url(
                wiki_api_url,
                timeout=5.0,
                headers={"User-Agent": "PromptIQ-ResearchEngine/1.0 (academic; open-source)"},
            )

            if resp.status_code == 200:
                data = resp.json()
                search_items = data.get("query", {}).get("search", [])
                for item in search_items[:max_results]:
                    title = item.get("title", "")
                    raw_snippet = item.get("snippet", "")
                    clean_snippet = sanitize_untrusted_search_content(raw_snippet)

                    page_slug = urllib.parse.quote(title.replace(" ", "_"))
                    source_url = f"https://en.wikipedia.org/wiki/{page_slug}"
                    try:
                        validate_and_sanitize_url(source_url)
                    except Exception as url_err:
                        logger.debug(
                            "Skipping unvalidated search result URL '%s': %s", source_url, url_err
                        )
                        continue

                    content = clean_snippet or f"Summary of {title}"
                    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                    results.append(
                        {
                            "url": source_url,
                            "title": title,
                            "publisher": "Wikimedia / Wikipedia Foundation",
                            "source_type": "official_docs",
                            "publication_date": item.get("timestamp", "")[:10] or "2024-01-01",
                            "content": content,
                            "content_hash": content_hash,
                            "reliability_tier": "tier_1_encyclopedia",
                            "locator": f"Page: {title}",
                            "provenance": "live_web",
                            "is_mock": False,
                        }
                    )

            if results:
                logger.info(
                    f"Live search retrieved {len(results)} authoritative sources for query '{query}'"
                )
                return results

        except Exception as e:
            logger.warning(
                f"Live search query failed or timed out: {e}. Falling back to deterministic knowledge base."
            )

        # Fallback to mock connector if live query yielded no results or network is offline
        if self.fallback:
            fallback_results = await self.fallback.search(query, max_results=max_results)
            for res in fallback_results:
                res["provenance"] = "simulated_mock"
                res["is_mock"] = True
                content = res.get("content", "")
                res["content_hash"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
                res["reliability_tier"] = "tier_3_simulated"
            return fallback_results

        return []
