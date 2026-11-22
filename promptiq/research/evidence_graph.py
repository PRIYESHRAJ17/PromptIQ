"""Evidence Graph and Citation Verification Engine with Character-Offset Grounding."""

import hashlib
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SourceReliabilityTier(StrEnum):
    TIER_1_PRIMARY = "tier_1_primary"          # Official docs, specifications, peer-reviewed
    TIER_2_SECONDARY = "tier_2_secondary"      # Industry standards, verified technical benchmarks
    TIER_3_COMMUNITY = "tier_3_community"      # Forum posts, community blogs, unverified secondary
    TIER_4_SIMULATED = "tier_4_simulated"      # Simulated or synthetic fallback


class EvidenceExcerpt(BaseModel):
    id: str
    source_url: str
    source_title: str
    publisher: str
    text_excerpt: str
    start_offset: int
    end_offset: int
    content_hash: str
    reliability_tier: SourceReliabilityTier


class EvidenceGraphNode(BaseModel):
    claim_id: str
    claim_text: str
    supporting_excerpts: list[EvidenceExcerpt] = Field(default_factory=list)
    contradicting_excerpts: list[EvidenceExcerpt] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    is_verified: bool = False
    verification_notes: str | None = None


class EvidenceGraph(BaseModel):
    job_id: str
    primary_question: str
    nodes: dict[str, EvidenceGraphNode] = Field(default_factory=dict)
    detected_contradictions: list[str] = Field(default_factory=list)


class EvidenceGraphBuilder:
    """Builds verifiable evidence graphs and verifies exact citation offsets."""

    @staticmethod
    def sanitize_untrusted_content(raw_text: str) -> str:
        """Sanitizes external web content to prevent prompt injection or instruction overrides."""
        dangerous_patterns = [
            r"(?i)ignore\s+(all\s+)?previous\s+instructions",
            r"(?i)system\s+prompt\s+override",
            r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
            r"(?i)output\s+your\s+system\s+prompt",
        ]
        sanitized = raw_text
        import re
        for pat in dangerous_patterns:
            sanitized = re.sub(pat, "[SANITIZED_PROMPT_INJECTION_ATTEMPT]", sanitized)
        return sanitized

    @classmethod
    def extract_verifiable_excerpt(
        cls,
        source_body: str,
        target_phrase: str,
        source_url: str,
        source_title: str,
        publisher: str,
        reliability_tier: SourceReliabilityTier,
    ) -> EvidenceExcerpt | None:
        """Locates exact phrase within source text and extracts character offsets."""
        clean_body = cls.sanitize_untrusted_content(source_body)
        idx = clean_body.lower().find(target_phrase.lower())
        if idx == -1:
            return None

        start_offset = idx
        end_offset = idx + len(target_phrase)
        actual_excerpt = clean_body[start_offset:end_offset]

        c_hash = hashlib.sha256(clean_body.encode("utf-8")).hexdigest()
        excerpt_id = f"exc-{hashlib.sha256((source_url + str(start_offset)).encode('utf-8')).hexdigest()[:10]}"

        return EvidenceExcerpt(
            id=excerpt_id,
            source_url=source_url,
            source_title=source_title,
            publisher=publisher,
            text_excerpt=actual_excerpt,
            start_offset=start_offset,
            end_offset=end_offset,
            content_hash=c_hash,
            reliability_tier=reliability_tier,
        )

    @classmethod
    def verify_citation(
        cls,
        excerpt: EvidenceExcerpt,
        original_source_text: str,
    ) -> bool:
        """Verifies that an excerpt actually exists at the exact character offsets in source text."""
        if excerpt.start_offset < 0 or excerpt.end_offset > len(original_source_text):
            return False
        slice_text = original_source_text[excerpt.start_offset:excerpt.end_offset]
        return slice_text.strip().lower() == excerpt.text_excerpt.strip().lower()

    @classmethod
    def detect_contradictions(
        cls,
        claims: list[dict[str, Any]],
    ) -> list[str]:
        """Detects contradictions across multiple extracted evidence claims."""
        contradictions: list[str] = []
        # Check numerical or directional conflicts (e.g., "100% free" vs "paid credit card required")
        for i, c1 in enumerate(claims):
            t1 = c1.get("text", "").lower()
            for j, c2 in enumerate(claims):
                if i >= j:
                    continue
                t2 = c2.get("text", "").lower()

                # Free vs Paid conflict
                if ("zero cost" in t1 or "free tier" in t1) and ("credit card required" in t2 or "paid billing" in t2):
                    contradictions.append(
                        f"Contradiction between Source '{c1.get('publisher')}' and '{c2.get('publisher')}': One claims zero-cost, other requires billing."
                    )
                # Rate limit conflict
                if "rate limit" in t1 and "rate limit" in t2 and t1 != t2:
                    if any(w in t1 for w in ["30 rpm", "15 rpm"]) and any(w in t2 for w in ["unlimited", "1000 rpm"]):
                        contradictions.append(
                            f"Contradiction on rate limits: '{t1[:60]}' vs '{t2[:60]}'"
                        )

        return contradictions
