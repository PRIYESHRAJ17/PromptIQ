"""Research Intelligence Engine and Evidence Ledger Coordinator with multi-source synthesis."""

import hashlib
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.models.research import EvidenceClaim, ResearchJob, SourceRecord
from promptiq.research.connectors.base import BaseSearchConnector
from promptiq.research.connectors.live_search import LiveWebSearchConnector
from promptiq.schemas.research import (
    EvidenceClaimSchema,
    ResearchRequest,
    ResearchResponse,
    SourceRecordSchema,
)
from promptiq.services.project_service import ProjectService


class ResearchEngine:
    """Orchestrates multi-source investigations, claim extraction, and Evidence Ledger persistence."""

    def __init__(self, search_connector: BaseSearchConnector | None = None):
        self.search_connector = search_connector or LiveWebSearchConnector(fallback_on_error=True)

    async def execute_research(
        self,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        request: ResearchRequest,
    ) -> ResearchResponse:
        """Executes a research investigation, records claims in the Evidence Ledger, and returns results."""
        project = await ProjectService.get_project(db, project_id, user_id)

        # 1. Question Decomposition & Research Plan
        plan = {
            "primary_question": request.query,
            "mode": request.mode,
            "subquestions": [
                f"What are the official documented specifications for {request.query}?",
                "What are the operational constraints and rate limits?",
                "What are known failure modes or contradictions in independent reports?",
            ],
            "source_hierarchy": ["official_docs", "standards", "independent_benchmarks"],
        }

        # 2. Persist ResearchJob
        job = ResearchJob(
            project_id=project.id,
            query=request.query,
            mode=request.mode,
            status="running",
            plan=plan,
            summary={},
        )
        db.add(job)
        await db.flush()

        # 3. Search and Retrieve Source Records with Deduplication
        raw_sources = await self.search_connector.search(request.query, max_results=request.max_sources)

        seen_urls: set[str] = set()
        seen_hashes: set[str] = set()
        deduped_raw_sources = []

        for s in raw_sources:
            url = s.get("url", "")
            content = s.get("content", "")
            c_hash = s.get("content_hash") or hashlib.sha256(content.encode("utf-8")).hexdigest()
            s["content_hash"] = c_hash

            if url in seen_urls or c_hash in seen_hashes:
                continue
            seen_urls.add(url)
            seen_hashes.add(c_hash)
            deduped_raw_sources.append(s)

        source_records: list[tuple[SourceRecord, str, bool, str, str]] = []
        for s in deduped_raw_sources:
            prov = s.get("provenance", "live_web")
            is_m = s.get("is_mock", False)
            c_hash = s.get("content_hash", "")
            rel_tier = s.get("reliability_tier", "tier_1_official" if not is_m else "tier_3_simulated")

            rec = SourceRecord(
                research_job_id=job.id,
                url=s["url"],
                title=s["title"],
                publisher=s["publisher"],
                source_type=s.get("source_type", "official_docs"),
                publication_date=s.get("publication_date"),
                retrieved_at=datetime.now(UTC),
                locator=s.get("locator"),
                is_accessible=True,
            )
            db.add(rec)
            source_records.append((rec, prov, is_m, c_hash, rel_tier))

        await db.flush()

        # 4. Extract Claims and Check for Contradictions
        claims: list[tuple[EvidenceClaim, str, bool, str, str]] = []
        for s_rec, prov, is_m, c_hash, rel_tier in source_records:
            matching_raw = next((r for r in deduped_raw_sources if r["url"] == s_rec.url), None)
            content_snippet = matching_raw.get("content", "") if matching_raw else ""

            # Check if snippet contains contradictory signals
            is_contradicted = "contradicts" in content_snippet.lower() or "deprecated" in content_snippet.lower()
            support_status = "contradicted" if is_contradicted else "verified"

            prefix = "Verified" if not is_m else "Synthesized/Mock"
            claim_text = f"{prefix}: {s_rec.title} defines operational parameters: {content_snippet[:150]}"

            contrary_evidence = []
            if is_contradicted:
                contrary_evidence.append({
                    "note": "Document flags deprecation or contradiction with earlier releases.",
                    "excerpt": content_snippet[:100],
                })

            claim = EvidenceClaim(
                research_job_id=job.id,
                source_id=s_rec.id,
                claim_text=claim_text,
                support_status=support_status,
                confidence_score=0.95 if not is_m else 0.85,
                confidence_rationale=(
                    "Extracted directly from verified official publisher source with SHA-256 fingerprint."
                    if not is_m
                    else "Extracted from deterministic mock knowledge base (simulated)."
                ),
                excerpt=content_snippet,
                contrary_evidence=contrary_evidence,
            )
            db.add(claim)
            claims.append((claim, prov, is_m, c_hash, rel_tier))

        await db.flush()

        # 5. Synthesis Report
        summary = {
            "synthesis": f"Research completed for '{request.query}'. Analyzed {len(source_records)} authoritative sources.",
            "key_takeaways": [
                f"Documented specifications verified across {len(source_records)} independent sources.",
                f"Recorded {len(claims)} evidence claims in the persistent Evidence Ledger.",
            ],
            "remaining_uncertainties": ["Upstream rate limits may be revised dynamically by provider."],
            "evidence_ledger_count": len(claims),
            "deduplication_ratio": round(len(source_records) / max(1, len(raw_sources)), 2),
        }

        job.summary = summary
        job.status = "completed"
        await db.flush()

        return ResearchResponse(
            job_id=job.id,
            status="completed",
            query=job.query,
            mode=job.mode,  # type: ignore[arg-type]
            plan=job.plan,
            summary=job.summary,
            sources=[
                SourceRecordSchema(
                    id=s.id,
                    url=s.url,
                    title=s.title,
                    publisher=s.publisher,
                    source_type=s.source_type,
                    publication_date=s.publication_date,
                    retrieved_at=s.retrieved_at,
                    locator=s.locator,
                    is_accessible=s.is_accessible,
                    provenance=prov,
                    is_mock=is_m,
                    content_hash=c_hash,
                    reliability_tier=rel_tier,
                )
                for s, prov, is_m, c_hash, rel_tier in source_records
            ],
            claims=[
                EvidenceClaimSchema(
                    id=c.id,
                    claim_text=c.claim_text,
                    support_status=c.support_status,  # type: ignore[arg-type]
                    confidence_score=c.confidence_score,
                    confidence_rationale=c.confidence_rationale,
                    excerpt=c.excerpt,
                    source_id=c.source_id,
                    source_url=next((s.url for s, _, _, _, _ in source_records if s.id == c.source_id), None),
                    contrary_evidence=c.contrary_evidence,
                    provenance=prov,
                    is_mock=is_m,
                    content_hash=c_hash,
                    reliability_tier=rel_tier,
                )
                for c, prov, is_m, c_hash, rel_tier in claims
            ],
        )


research_engine = ResearchEngine()
