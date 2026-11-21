"""Adaptive Discovery Coordinator managing progressive disclosure and anti-fatigue checks."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import NotFoundError
from promptiq.core.security import validate_and_sanitize_url
from promptiq.discovery.extractor import ContextExtractor
from promptiq.discovery.software_stages import SOFTWARE_STAGES, get_software_stage_questions
from promptiq.discovery.task_paths import get_task_questions
from promptiq.discovery.task_registry import TaskCategoryRegistry
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.models.discovery import DiscoverySession
from promptiq.schemas.discovery import (
    DiscoveryQuestion,
    DiscoverySessionResponse,
    InitialIntakeRequest,
)
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService


class AdaptiveDiscoveryEngine:
    """Orchestrates conversational intake, depth-adaptive questioning, and requirement extraction."""

    @classmethod
    def detect_contradictions(cls, session: DiscoverySession) -> list[str]:
        """Detects contradictions between intake constraints and submitted answers."""
        contradictions: list[str] = []
        intake = session.initial_intake or {}
        answers = session.answers or {}
        constraints = [c.lower() for c in intake.get("constraints", [])]
        goal = intake.get("goal", "").lower()
        context_text = (intake.get("context_text") or "").lower()

        combined_context = f"{goal} {' '.join(constraints)} {context_text}"

        # 1. Frontend exclusion vs UI surface request
        no_frontend = any("no frontend" in c or "backend only" in c or "no ui" in c for c in [combined_context])
        surfaces = str(answers.get("surfaces_required", "")).lower()
        visual_dir = str(answers.get("visual_direction", "")).lower()
        if no_frontend and ("react" in visual_dir or "web workspace" in surfaces or "mobile companion" in surfaces):
            contradictions.append(
                "Contradiction: Project specifies strict backend-only/no-frontend constraint, but answers request UI surfaces."
            )

        # 2. Free tier / Zero-price constraint vs paid cloud infrastructure
        zero_cost = any("zero-price" in c or "free" in c or "zero cost" in c or "₹0" in c for c in [combined_context])
        tech_pref = str(answers.get("tech_stack_preference", "")).lower()
        if zero_cost and ("aws fargate" in tech_pref or "dynamodb global" in tech_pref or "paid tier" in tech_pref):
            contradictions.append(
                "Contradiction: Strict zero-cost invariant specified, but technical stack preference requests billable commercial infrastructure."
            )

        # 3. Conflicting database paradigms
        if "sqlite" in tech_pref and "distributed multi-region postgresql" in tech_pref:
            contradictions.append(
                "Contradiction: Embedded local SQLite requested concurrently with distributed multi-region PostgreSQL."
            )

        # 4. Invariant: No Local Inference
        all_answers_str = " ".join(str(v).lower() for v in answers.values())
        if "ollama" in all_answers_str or "llama.cpp" in all_answers_str or "local gpu" in all_answers_str:
            contradictions.append(
                "Contradiction: Local model inference requested, which violates PromptIQ's centrally hosted gateway invariant."
            )

        # 5. Invariant: No User API Keys / BYOK
        if "user api key" in all_answers_str or "byok" in all_answers_str or "enter openai key" in all_answers_str:
            contradictions.append(
                "Contradiction: User API key input requested, violating PromptIQ's zero-price / zero-BYOK policy."
            )

        return contradictions

    @classmethod
    def detect_missing_high_impact_info(cls, session: DiscoverySession) -> list[str]:
        """Identifies high-impact unknowns or missing requirements based on task depth and type."""
        answers = session.answers or {}
        task_type = getattr(session, "task_type", None) or "software_project"
        depth = getattr(session, "depth", None) or "guided"

        # Check TaskCategoryRegistry for dynamic task family requirements
        missing = TaskCategoryRegistry.detect_missing_info(task_type, answers, depth=depth)

        # Fallback / software-specific additions for deep software workflows
        if task_type == "software_project" and depth == "deep":
            if "auth_requirements" not in answers and "Authentication and multi-tenant authorization boundaries (Stage I)" not in missing:
                missing.append("Authentication and multi-tenant authorization boundaries (Stage I)")
            if "validation_rules" not in answers and "Domain business rules and input validation constraints (Stage D)" not in missing:
                missing.append("Domain business rules and input validation constraints (Stage D)")

        return missing


    @classmethod
    async def start_session(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        intake: InitialIntakeRequest,
    ) -> DiscoverySessionResponse:
        """Initializes a new discovery session from the first 4 inputs."""
        # Verify tenant access before creating discovery session
        await ProjectService.get_project(db, project_id, user_id)

        # 1. SSRF check on reference URLs
        for url in intake.context_urls:
            validate_and_sanitize_url(url)

        # 2. Extract initial facts from supplied context text and files
        extracted_facts = []
        if intake.context_text:
            extracted_facts.extend(ContextExtractor.extract_facts_from_text(intake.context_text))

        if intake.existing_files:
            for file_info in intake.existing_files:
                f_name = file_info.get("filename", "unknown_file")
                f_content = file_info.get("content", "")
                if f_content:
                    extracted_facts.extend(
                        ContextExtractor.extract_facts_from_text(f_content, source_label=f"file:{f_name}")
                    )

        session = DiscoverySession(
            project_id=project_id,
            task_type=intake.task_type,
            depth=intake.depth,
            initial_intake=intake.model_dump(),
            answers={},
            extracted_facts=extracted_facts,
            current_stage="stage_a" if intake.task_type == "software_project" and intake.depth == "deep" else "task_details",
            is_completed=False,
        )
        db.add(session)
        await db.flush()

        # Seed initial goal into Constitution
        constitution = await ConstitutionService.get_current_constitution(db, project_id, user_id)
        current_goals = list(constitution.goals)
        if intake.goal not in current_goals:
            current_goals.append(intake.goal)
            constitution.goals = current_goals

        # Seed explicit constraints into Constitution
        if intake.constraints:
            scope = dict(constitution.scope or {})
            out_of_scope = list(scope.get("out_of_scope", []))
            for c in intake.constraints:
                if c not in out_of_scope:
                    out_of_scope.append(c)
            scope["out_of_scope"] = out_of_scope
            constitution.scope = scope

        # Generate initial candidate requirements from goal
        initial_reqs = list(constitution.requirements)
        initial_reqs.append({
            "id": "REQ-CORE-001",
            "text": f"Core objective: {intake.goal}",
            "category": "functional",
            "priority": "P0",
            "status": "confirmed",
            "provenance": "user_provided",
            "source_reference": "initial_intake",
            "acceptance_criteria": "Observable delivery of stated goal",
        })
        constitution.requirements = initial_reqs
        await db.flush()

        next_questions = cls.get_next_questions(session)

        return DiscoverySessionResponse(
            id=session.id,
            project_id=session.project_id,
            task_type=session.task_type,
            depth=session.depth,
            current_stage=session.current_stage,
            is_completed=session.is_completed,
            initial_intake=session.initial_intake,
            answers=session.answers,
            extracted_facts=session.extracted_facts,
            identified_contradictions=cls.detect_contradictions(session),
            missing_high_impact_info=cls.detect_missing_high_impact_info(session),
            next_questions=next_questions,
        )

    @classmethod
    def get_next_questions(cls, session: DiscoverySession) -> list[DiscoveryQuestion]:
        """Calculates next questions based on depth, task type, and answered history."""
        if session.is_completed:
            return []

        answered_keys = set(session.answers.keys())

        if session.depth == "quick":
            # Quick mode: ask at most 1-2 high-priority questions
            all_questions = get_task_questions(session.task_type, answered_keys)
            return all_questions[:1]

        elif session.depth == "guided":
            # Guided mode: present standard task questions
            return get_task_questions(session.task_type, answered_keys)[:3]

        else:
            # Deep mode: full multi-stage interview
            if session.task_type == "software_project":
                stage_questions = get_software_stage_questions(session.current_stage, answered_keys)
                if not stage_questions:
                    # Advance to next software stage
                    cls._advance_software_stage(session)
                    return get_software_stage_questions(session.current_stage, answered_keys)
                return stage_questions
            else:
                return get_task_questions(session.task_type, answered_keys)

    @classmethod
    def _advance_software_stage(cls, session: DiscoverySession) -> None:
        stage_ids = [s["id"] for s in SOFTWARE_STAGES]
        try:
            curr_idx = stage_ids.index(session.current_stage)
            if curr_idx + 1 < len(stage_ids):
                session.current_stage = stage_ids[curr_idx + 1]
            else:
                session.current_stage = "completed"
                session.is_completed = True
        except ValueError:
            session.current_stage = "completed"
            session.is_completed = True

    @classmethod
    async def submit_answers(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
        submitted_answers: dict[str, Any],
        project_id: str | None = None,
    ) -> DiscoverySessionResponse:
        """Processes submitted answers, infers new requirements, and updates Constitution."""
        stmt = select(DiscoverySession).where(DiscoverySession.id == session_id)
        if project_id:
            stmt = stmt.where(DiscoverySession.project_id == project_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundError("DiscoverySession", session_id)

        # Verify tenant access before updating session
        await ProjectService.get_project(db, session.project_id, user_id)

        # Merge answers
        updated_answers = dict(session.answers)
        updated_answers.update(submitted_answers)
        session.answers = updated_answers

        # Convert high-value answers to Constitution requirements
        constitution = await ConstitutionService.get_current_constitution(db, session.project_id, user_id)
        reqs = list(constitution.requirements)

        for q_id, ans in submitted_answers.items():
            if not ans:
                continue
            ans_str = str(ans)
            if q_id.startswith("confirm_inferred_"):
                # Handle user confirmation or rejection of inferred requirements
                inf_req_id = q_id.replace("confirm_inferred_", "")
                for r in reqs:
                    if r.get("id") == inf_req_id:
                        if ans in (True, "yes", "confirm", "confirmed"):
                            r["status"] = "confirmed"
                            r["provenance"] = "user_provided"
                        else:
                            r["status"] = "rejected"
            elif q_id in ("problem_statement", "must_have_features", "validation_rules", "acceptance_criteria"):
                req_id = f"REQ-DISC-{len(reqs) + 1:03d}"
                reqs.append({
                    "id": req_id,
                    "text": ans_str,
                    "category": "functional",
                    "priority": "P0" if q_id == "must_have_features" else "P1",
                    "status": "confirmed",
                    "provenance": "user_provided",
                    "source_reference": f"discovery_answer:{q_id}",
                    "acceptance_criteria": ans_str if q_id == "acceptance_criteria" else None,
                })
            elif q_id == "explicit_exclusions":
                scope = dict(constitution.scope or {})
                out_of_scope = list(scope.get("out_of_scope", []))
                out_of_scope.append(ans_str)
                scope["out_of_scope"] = out_of_scope
                constitution.scope = scope
            elif q_id == "visual_direction":
                ux_spec = dict(constitution.ux_specs or {})
                ux_spec["visual_direction"] = ans_str
                constitution.ux_specs = ux_spec
            elif q_id == "tech_stack_preference":
                tech_dir = dict(constitution.technical_direction or {})
                tech_dir["preferred_stack"] = [s.strip() for s in ans_str.split(",") if s.strip()]
                constitution.technical_direction = tech_dir

        constitution.requirements = reqs

        # Call intelligence gateway to infer missing requirements if appropriate
        inference_req = InferenceRequest(
            messages=[GatewayMessage(role="user", content=f"Analyze project answers: {updated_answers}")],
            system_instruction="Identify implicit technical requirements and return JSON.",
            task_context="discovery",
            user_id=user_id,
        )
        infer_resp = await inference_gateway.generate(inference_req)
        if infer_resp.structured_data and isinstance(infer_resp.structured_data, dict):
            inferred_reqs = infer_resp.structured_data.get("inferred_requirements", [])
            for inf in inferred_reqs:
                # Add inferred requirements labeled with provenance='inferred'
                req_id = f"REQ-INF-{len(reqs) + 1:03d}"
                reqs.append({
                    "id": req_id,
                    "text": inf.get("text", "Inferred system requirement"),
                    "category": inf.get("category", "functional"),
                    "priority": inf.get("priority", "P2"),
                    "status": "proposed",
                    "provenance": "inferred",
                    "source_reference": "promptiq_adaptive_inference",
                    "acceptance_criteria": None,
                })
            constitution.requirements = reqs

        await db.flush()

        next_questions = cls.get_next_questions(session)
        if not next_questions:
            session.is_completed = True

        return DiscoverySessionResponse(
            id=session.id,
            project_id=session.project_id,
            task_type=session.task_type,
            depth=session.depth,
            current_stage=session.current_stage,
            is_completed=session.is_completed,
            initial_intake=session.initial_intake,
            answers=session.answers,
            extracted_facts=session.extracted_facts,
            identified_contradictions=cls.detect_contradictions(session),
            missing_high_impact_info=cls.detect_missing_high_impact_info(session),
            next_questions=next_questions,
        )
