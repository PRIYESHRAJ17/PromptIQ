"""Context extraction from pasted text, documents, and reference URLs."""

import re
from typing import Any

from promptiq.core.security import sanitize_untrusted_input


class ContextExtractor:
    """Extracts structured entities, tech preferences, and potential requirements from raw context."""

    TECH_PATTERNS = {
        "python": re.compile(
            r"\b(python|fastapi|django|flask|pydantic|sqlalchemy)\b", re.IGNORECASE
        ),
        "typescript": re.compile(
            r"\b(typescript|node|nodejs|react|nextjs|express)\b", re.IGNORECASE
        ),
        "postgresql": re.compile(r"\b(postgres|postgresql|pgvector)\b", re.IGNORECASE),
        "sqlite": re.compile(r"\b(sqlite|aiosqlite)\b", re.IGNORECASE),
        "docker": re.compile(r"\b(docker|container|compose|k8s|kubernetes)\b", re.IGNORECASE),
        "telegram": re.compile(r"\b(telegram|bot\s*api|telebot|aiogram)\b", re.IGNORECASE),
        "mcp": re.compile(r"\b(mcp|model\s*context\s*protocol)\b", re.IGNORECASE),
    }

    ROLE_PATTERNS = re.compile(
        r"\b(user|admin|operator|developer|student|researcher|customer)\b", re.IGNORECASE
    )

    @classmethod
    def extract_facts_from_text(
        cls, text: str, source_label: str = "pasted_text"
    ) -> list[dict[str, Any]]:
        """Parses raw text and extracts candidate facts and tags."""
        clean_text = sanitize_untrusted_input(text)
        facts: list[dict[str, Any]] = []

        if not clean_text:
            return facts

        # Detect technologies mentioned
        detected_tech = []
        for tech_name, pattern in cls.TECH_PATTERNS.items():
            if pattern.search(clean_text):
                detected_tech.append(tech_name)

        if detected_tech:
            facts.append(
                {
                    "fact": f"Project references technologies: {', '.join(detected_tech)}",
                    "category": "technical",
                    "provenance": "file_extracted" if "file" in source_label else "user_provided",
                    "source": source_label,
                }
            )

        # Detect user roles mentioned
        roles = set(cls.ROLE_PATTERNS.findall(clean_text))
        if roles:
            facts.append(
                {
                    "fact": f"Identified potential user roles: {', '.join(roles)}",
                    "category": "users",
                    "provenance": "file_extracted" if "file" in source_label else "user_provided",
                    "source": source_label,
                }
            )

        # Capture raw text snippet as reference
        snippet = clean_text[:300].strip()
        facts.append(
            {
                "fact": f"Context excerpt: '{snippet}'",
                "category": "context_snippet",
                "provenance": "file_extracted" if "file" in source_label else "user_provided",
                "source": source_label,
            }
        )

        return facts
