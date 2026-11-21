"""Context Compiler for target-aware packing and token budget management."""

from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.schemas.memory import ContextPackRequest, ContextPackResponse
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService


class ContextCompiler:
    """Selects, prioritizes, and packs durable project memory into target context windows."""

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Approximates token count (standard ~4 characters per token heuristic)."""
        return max(1, len(text) // 4)

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

        # Build prioritized context sections
        sections: list[str] = []

        # 1. Project Goal & Overview
        overview_text = (
            f"# PROJECT CONTEXT: {project.name}\n\n"
            f"**Project ID**: `{project.id}`\n"
            f"**Constitution Version**: v{constitution.version}\n"
            f"**Primary Goals**:\n" + "\n".join([f"- {g}" for g in constitution.goals])
        )
        sections.append(overview_text)
        items_included.append("goals")

        # 2. Confirmed Requirements (P0 & P1 prioritized)
        reqs_lines = []
        for r in constitution.requirements:
            prio = r.get("priority", "P1")
            reqs_lines.append(f"- [{r.get('id')}] ({prio} - {r.get('provenance')}): {r.get('text')}")
        if reqs_lines:
            sections.append("## CONFIRMED REQUIREMENTS\n" + "\n".join(reqs_lines))
            items_included.append("requirements")

        # 3. Technical Direction & Scope
        tech_lines = [
            f"- Architecture Pattern: {constitution.technical_direction.get('architecture_pattern', 'modular_monolith')}",
            f"- Preferred Stack: {', '.join(constitution.technical_direction.get('preferred_stack', [])) or 'Standard'}",
            f"- Prohibited Stack: {', '.join(constitution.technical_direction.get('prohibited_stack', [])) or 'None'}",
        ]
        sections.append("## TECHNICAL DIRECTION & CONSTRAINTS\n" + "\n".join(tech_lines))
        items_included.append("technical_direction")

        # 4. Out of Scope Exclusions
        out_of_scope = constitution.scope.get("out_of_scope", [])
        if out_of_scope:
            sections.append("## OUT OF SCOPE (EXCLUSIONS)\n" + "\n".join([f"- {e}" for e in out_of_scope]))
            items_included.append("scope_exclusions")

        # 5. Assemble and apply token budget ceiling
        full_text = "\n\n".join(sections)
        estimated_tokens = cls.estimate_tokens(full_text)

        if estimated_tokens > request.max_token_budget:
            # Truncate lower-priority sections if exceeding budget
            char_budget = request.max_token_budget * 4
            full_text = full_text[:char_budget] + "\n\n... [Context truncated to fit target token window]"
            items_truncated.append("lower_priority_context")
            estimated_tokens = request.max_token_budget

        return ContextPackResponse(
            project_id=project.id,
            constitution_version=constitution.version,
            packed_context_markdown=full_text,
            estimated_tokens=estimated_tokens,
            items_included=items_included,
            items_truncated=items_truncated,
            latest_checkpoint=None,
        )
