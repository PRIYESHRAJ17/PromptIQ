"""Adaptive Discovery Coordinator managing progressive disclosure and anti-fatigue checks."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import NotFoundError
from promptiq.discovery.extractor import ContextExtractor
from promptiq.discovery.software_stages import SOFTWARE_STAGES, get_software_stage_questions
from promptiq.discovery.task_paths import get_task_questions
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.models.discovery import DiscoverySession
from promptiq.schemas.discovery import (
    DiscoveryQuestion,
    DiscoverySessionResponse,
    InitialIntakeRequest,
)
from promptiq.services.constitution_service import ConstitutionService


class AdaptiveDiscoveryEngine:
    """Orchestrates conversational intake, depth-adaptive questioning, and requirement extraction."""

    @classmethod
    async def start_session(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        intake: InitialIntakeRequest,
    ) -> DiscoverySessionResponse:
        """Initializes a new discovery session from the first 4 inputs."""
        # Extract initial facts from supplied context text
        extracted_facts = []
        if intake.context_text:
            extracted_facts = ContextExtractor.extract_facts_from_text(intake.context_text)

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
    ) -> DiscoverySessionResponse:
        """Processes submitted answers, infers new requirements, and updates Constitution."""
        stmt = select(DiscoverySession).where(DiscoverySession.id == session_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundError("DiscoverySession", session_id)

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
            if q_id in ("problem_statement", "must_have_features", "validation_rules", "acceptance_criteria"):
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
                scope = dict(constitution.scope)
                out_of_scope = list(scope.get("out_of_scope", []))
                out_of_scope.append(ans_str)
                scope["out_of_scope"] = out_of_scope
                constitution.scope = scope
            elif q_id == "visual_direction":
                ux_spec = dict(constitution.ux_specs)
                ux_spec["visual_direction"] = ans_str
                constitution.ux_specs = ux_spec
            elif q_id == "tech_stack_preference":
                tech_dir = dict(constitution.technical_direction)
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
            next_questions=next_questions,
        )
