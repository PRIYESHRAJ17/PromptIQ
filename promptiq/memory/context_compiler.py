"""Context Compiler for target-aware packing, token budgeting, and relevance filtering."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.models.memory import Checkpoint
from promptiq.schemas.memory import CheckpointResponse, ContextPackRequest, ContextPackResponse
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService


class ContextCompiler:
    """Selects, prioritizes, and packs durable project memory into target context windows."""

    PRIORITY_LEVELS = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Approximates token count (standard ~4 characters per token heuristic)."""
        return max(1, len(text) // 4)

    @classmethod
    def detect_memory_conflicts(
        cls, decisions: list[dict[str, Any]], requirements: list[dict[str, Any]]
    ) -> list[str]:
        """Detects contradictions between architectural decisions and requirement statements."""
        conflicts = []
        for d in decisions:
            d_text = (
                str(d.get("decision", "") if isinstance(d, dict) else getattr(d, "decision", ""))
                + " "
                + str(d.get("rationale", "") if isinstance(d, dict) else getattr(d, "rationale", ""))
            ).lower()
            d_id = str(d.get("id", "DEC") if isinstance(d, dict) else getattr(d, "id", "DEC"))

            for r in requirements:
                r_text = str(
                    r.get("text", "") if isinstance(r, dict) else getattr(r, "text", "")
                ).lower()
                r_id = str(r.get("id", "REQ") if isinstance(r, dict) else getattr(r, "id", "REQ"))

                if "no frontend" in d_text and any(
                    w in r_text for w in ["react", "web interface", "dashboard", "navbar"]
                ):
                    conflicts.append(
                        f"Decision '{d_id}' specifies no-frontend, but Requirement '{r_id}' requests UI components."
                    )
                if "sqlite" in d_text and "distributed postgres" in r_text:
                    conflicts.append(
                        f"Decision '{d_id}' specifies SQLite, but Requirement '{r_id}' requests distributed PostgreSQL."
                    )
        return conflicts

    @classmethod
    async def compile_context(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        request: ContextPackRequest,
    ) -> ContextPackResponse:
        """Compiles project constitution, requirements, and checkpoints into an optimized markdown block."""
        project = await ProjectService.get_project(db, project_id, user_id)
        constitution = await ConstitutionService.get_current_constitution(db, project_id, user_id)

        items_included: list[str] = []
        items_truncated: list[str] = []
        sections: list[str] = []

        # 1. Project Goal & Overview (Mandatory P0)
        overview_text = (
            f"# PROJECT CONTEXT: {project.name}\n\n"
            f"**Project ID**: `{project.id}`\n"
            f"**Constitution Version**: v{constitution.version}\n"
            f"**Primary Goals**:\n" + "\n".join([f"- {g}" for g in constitution.goals])
        )
        sections.append(overview_text)
        items_included.append("goals")

        # 2. Out of Scope Exclusions (Crucial for preventing stray generation)
        out_of_scope = constitution.scope.get("out_of_scope", [])
        if out_of_scope:
            sections.append(
                "## OUT OF SCOPE (NON-NEGOTIABLE EXCLUSIONS)\n"
                + "\n".join([f"- {e}" for e in out_of_scope])
            )
            items_included.append("scope_exclusions")

        # 3. Technical Direction & Architecture Pattern
        tech_lines = [
            f"- Architecture Pattern: {constitution.technical_direction.get('architecture_pattern', 'modular_monolith')}",
            f"- Preferred Stack: {', '.join(constitution.technical_direction.get('preferred_stack', [])) or 'Standard'}",
            f"- Prohibited Stack: {', '.join(constitution.technical_direction.get('prohibited_stack', [])) or 'None'}",
        ]
        sections.append("## TECHNICAL DIRECTION & CONSTRAINTS\n" + "\n".join(tech_lines))
        items_included.append("technical_direction")

        # 4. Filtered & Ranked Requirements
        max_prio_val = cls.PRIORITY_LEVELS.get(request.priority_cutoff.upper(), 2)
        raw_reqs = constitution.requirements or []

        filtered_reqs = []
        for r in raw_reqs:
            if isinstance(r, dict):
                prio = r.get("priority", "P1")
                prov = r.get("provenance", "user_provided")
                r_id = r.get("id")
                text = r.get("text", "")
            else:
                prio = getattr(r, "priority", "P1")
                prov = getattr(r, "provenance", "user_provided")
                r_id = getattr(r, "id", None)
                text = getattr(r, "text", "")

            # Filter by priority cutoff
            if cls.PRIORITY_LEVELS.get(prio, 1) > max_prio_val:
                continue

            # Filter by provenance if requested
            if request.provenance_filter and prov not in request.provenance_filter:
                continue

            # Relevance weighting
            relevance_score = 0
            if request.task_focus:
                focus_words = request.task_focus.lower().split()
                relevance_score = sum(1 for w in focus_words if w in text.lower())

            filtered_reqs.append(
                (relevance_score, cls.PRIORITY_LEVELS.get(prio, 1), r_id, prio, prov, text)
            )

        # Sort: highest relevance score first, then lowest priority value (P0 before P1)
        filtered_reqs.sort(key=lambda x: (-x[0], x[1]))

        reqs_lines = []
        for _, _, r_id, prio, prov, text in filtered_reqs:
            reqs_lines.append(f"- [{r_id}] ({prio} - {prov}): {text}")

        if reqs_lines:
            sections.append("## CONFIRMED REQUIREMENTS\n" + "\n".join(reqs_lines))
            items_included.append("requirements")

        # 5. Recorded Architectural Decisions
        decisions = constitution.decisions or []
        if decisions:
            dec_lines = []
            for d in decisions:
                d_id = d.get("id") if isinstance(d, dict) else getattr(d, "id", "")
                d_dec = d.get("decision") if isinstance(d, dict) else getattr(d, "decision", "")
                d_rat = d.get("rationale") if isinstance(d, dict) else getattr(d, "rationale", "")
                dec_lines.append(f"- [{d_id}] **{d_dec}**: {d_rat}")
            sections.append("## ARCHITECTURAL DECISIONS\n" + "\n".join(dec_lines))
            items_included.append("decisions")

        # 5.5 Accepted Risks & Open Questions
        risks = getattr(constitution, "risks", []) or []
        if risks:
            risk_lines = [
                f"- [{r.get('id', 'RSK')}] ({r.get('severity', 'medium')}): {r.get('description', '')}"
                for r in risks
            ]
            sections.append("## ACCEPTED RISKS\n" + "\n".join(risk_lines))
            items_included.append("risks")

        open_questions = getattr(constitution, "open_questions", []) or []
        if open_questions:
            q_lines = [
                f"- [{q.get('id', 'Q')}] {q.get('question', '')} (Impact: {q.get('impact', 'medium')})"
                for q in open_questions
            ]
            sections.append("## OPEN QUESTIONS\n" + "\n".join(q_lines))
            items_included.append("open_questions")

        # Memory Conflict Detection
        conflicts = cls.detect_memory_conflicts(decisions, raw_reqs)
        if conflicts:
            sections.append("## DETECTED MEMORY CONFLICTS\n" + "\n".join([f"- WARNING: {c}" for c in conflicts]))
            items_included.append("conflicts")

        # 6. Latest Checkpoint Snapshot
        stmt_cp = (
            select(Checkpoint)
            .where(Checkpoint.project_id == project_id)
            .order_by(Checkpoint.created_at.desc())
        )
        res_cp = await db.execute(stmt_cp)
        latest_cp = res_cp.scalar_one_or_none()
        latest_cp_response = None
        if latest_cp:
            latest_cp_response = CheckpointResponse.model_validate(latest_cp)
            cp_block = (
                f"## LATEST VERIFIED CHECKPOINT ({latest_cp.phase})\n"
                f"- Summary: {latest_cp.summary}\n"
                f"- Blockers: {', '.join(latest_cp.blockers) or 'None'}\n"
                f"- Next Actions: {', '.join(latest_cp.next_actions) or 'Proceed'}"
            )
            sections.append(cp_block)
            items_included.append("checkpoint")

        # 7. Token Budget Enforcement
        full_text = "\n\n".join(sections)
        estimated_tokens = cls.estimate_tokens(full_text)

        if estimated_tokens > request.max_token_budget:
            char_budget = request.max_token_budget * 4
            full_text = (
                full_text[:char_budget] + "\n\n... [Context truncated to fit target token window]"
            )
            items_truncated.append("lower_priority_context")
            estimated_tokens = request.max_token_budget

        return ContextPackResponse(
            project_id=project.id,
            constitution_version=constitution.version,
            packed_context_markdown=full_text,
            estimated_tokens=estimated_tokens,
            items_included=items_included,
            items_truncated=items_truncated,
            latest_checkpoint=latest_cp_response,
        )
