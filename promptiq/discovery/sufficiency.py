"""Information Sufficiency Evaluation and Decision-Value Ranking for Adaptive Discovery."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from promptiq.schemas.discovery import DiscoveryQuestion


class DiscoveryProfile(StrEnum):
    QUICK = "quick"
    GUIDED = "guided"
    DEEP = "deep"
    TECHNICAL = "technical"
    RESEARCH = "research"
    BUSINESS = "business"
    CREATIVE = "creative"
    AGENTIC = "agentic"


class SufficiencyAssessment(BaseModel):
    profile: DiscoveryProfile
    sufficiency_score: float = Field(ge=0.0, le=1.0)
    target_threshold: float
    is_sufficient: bool
    critical_information_gaps: list[str] = Field(default_factory=list)
    decision_value_ranked_questions: list[DiscoveryQuestion] = Field(default_factory=list)
    recorded_assumptions: list[str] = Field(default_factory=list)
    recommended_action: str  # "CONTINUE_DISCOVERY" or "PROCEED_TO_SPECIFICATION"


class InformationSufficiencyEvaluator:
    """Evaluates information completeness, computes decision value, and determines stop conditions."""

    PROFILE_THRESHOLDS: dict[DiscoveryProfile, float] = {
        DiscoveryProfile.QUICK: 0.60,
        DiscoveryProfile.GUIDED: 0.75,
        DiscoveryProfile.DEEP: 0.90,
        DiscoveryProfile.TECHNICAL: 0.85,
        DiscoveryProfile.RESEARCH: 0.85,
        DiscoveryProfile.BUSINESS: 0.80,
        DiscoveryProfile.CREATIVE: 0.75,
        DiscoveryProfile.AGENTIC: 0.90,
    }

    # Weight of critical architectural facets by profile
    CORE_FACETS = {
        "primary_objective": 0.25,
        "deliverables": 0.20,
        "constraints": 0.15,
        "technical_stack": 0.15,
        "security_or_permissions": 0.15,
        "acceptance_criteria": 0.10,
    }

    @classmethod
    def evaluate_sufficiency(
        cls,
        task_type: str,
        profile_name: str,
        intake: dict[str, Any],
        answers: dict[str, Any],
        candidate_questions: list[DiscoveryQuestion],
    ) -> SufficiencyAssessment:
        """Computes information sufficiency score and ranks candidate questions by decision value."""
        try:
            profile = DiscoveryProfile(profile_name.lower())
        except ValueError:
            profile = DiscoveryProfile.GUIDED

        threshold = cls.PROFILE_THRESHOLDS.get(profile, 0.75)

        # 1. Evaluate facet coverage
        answered_keys = set(answers.keys())
        goal = intake.get("goal") or ""
        context_text = intake.get("context_text") or ""
        constraints = intake.get("constraints") or []

        score = 0.0
        gaps: list[str] = []
        assumptions: list[str] = []

        # Primary Objective
        if goal and len(goal.strip()) > 10:
            score += cls.CORE_FACETS["primary_objective"]
        else:
            gaps.append("Primary objective lacks specificity")

        # Deliverables
        if any(
            k in answered_keys for k in ["deliverables", "must_have_features", "expected_outputs"]
        ):
            score += cls.CORE_FACETS["deliverables"]
        elif any(
            w in (goal + context_text).lower()
            for w in ["api", "prompt", "report", "pipeline", "schema"]
        ):
            score += cls.CORE_FACETS["deliverables"] * 0.75
            assumptions.append("Deliverables inferred from context keywords")
        else:
            gaps.append("Expected deliverable format and components unspecified")

        # Constraints & Invariants
        if constraints and len(constraints) > 0:
            score += cls.CORE_FACETS["constraints"]
        elif "explicit_exclusions" in answered_keys:
            score += cls.CORE_FACETS["constraints"]
        else:
            score += cls.CORE_FACETS["constraints"] * 0.5
            assumptions.append("Assuming standard zero-price and backend-only boundaries")

        # Technical Stack
        if "tech_stack_preference" in answered_keys or any(
            w in (goal + context_text).lower()
            for w in ["python", "fastapi", "postgres", "sqlite", "docker"]
        ):
            score += cls.CORE_FACETS["technical_stack"]
        else:
            if profile in (
                DiscoveryProfile.TECHNICAL,
                DiscoveryProfile.DEEP,
                DiscoveryProfile.AGENTIC,
            ):
                gaps.append("Technical runtime and database stack unspecified")
            else:
                score += cls.CORE_FACETS["technical_stack"] * 0.5
                assumptions.append("Defaulting to standard Python 3.13 / FastAPI stack")

        # Security & Permissions
        if any(
            k in answered_keys
            for k in ["auth_requirements", "tool_permissions", "security_boundaries"]
        ):
            score += cls.CORE_FACETS["security_or_permissions"]
        elif any(
            w in (goal + context_text).lower()
            for w in ["auth", "jwt", "rbac", "permission", "safe"]
        ):
            score += cls.CORE_FACETS["security_or_permissions"] * 0.75
        else:
            if profile in (DiscoveryProfile.AGENTIC, DiscoveryProfile.TECHNICAL):
                gaps.append("Security boundaries and tool execution permissions unspecified")
            else:
                score += cls.CORE_FACETS["security_or_permissions"] * 0.6
                assumptions.append("Standard least-privilege tenant isolation assumed")

        # Acceptance Criteria
        if "acceptance_criteria" in answered_keys:
            score += cls.CORE_FACETS["acceptance_criteria"]
        elif any(
            w in (goal + context_text).lower()
            for w in ["acceptance", "test", "verify", "benchmark"]
        ):
            score += cls.CORE_FACETS["acceptance_criteria"] * 0.7
        else:
            assumptions.append("Acceptance criteria derived from stated objectives")
            score += cls.CORE_FACETS["acceptance_criteria"] * 0.4

        # Add bonus for comprehensive answers
        answer_count = len([v for v in answers.values() if v])
        if answer_count >= 5:
            score += 0.10
        elif answer_count >= 3:
            score += 0.05

        normalized_score = max(0.1, min(1.0, round(score, 2)))
        is_sufficient = normalized_score >= threshold

        # 2. Decision-Value Ranking for candidate questions
        # Questions addressing critical gaps have highest decision value
        ranked_questions = []
        for q in candidate_questions:
            q_id = q.id
            if q_id in answered_keys:
                continue

            # Compute decision value weight
            decision_value = 0.5
            if any(
                gap_word in q.question.lower()
                for gap_word in ["auth", "permission", "stack", "database", "security"]
            ):
                decision_value = 0.95
            elif any(
                gap_word in q.question.lower()
                for gap_word in ["feature", "deliverable", "output", "format"]
            ):
                decision_value = 0.85
            elif any(
                gap_word in q.question.lower()
                for gap_word in ["performance", "latency", "scale", "volume"]
            ):
                decision_value = 0.70
            else:
                decision_value = 0.50

            # Boost if question matches explicit gaps
            for gap in gaps:
                if any(w in q.question.lower() for w in gap.lower().split() if len(w) > 4):
                    decision_value += 0.15

            ranked_questions.append((decision_value, q))

        # Sort descending by decision value
        ranked_questions.sort(key=lambda x: x[0], reverse=True)
        final_questions = [q for _, q in ranked_questions]

        recommended_action = "PROCEED_TO_SPECIFICATION" if is_sufficient else "CONTINUE_DISCOVERY"

        return SufficiencyAssessment(
            profile=profile,
            sufficiency_score=normalized_score,
            target_threshold=threshold,
            is_sufficient=is_sufficient,
            critical_information_gaps=gaps,
            decision_value_ranked_questions=final_questions,
            recorded_assumptions=assumptions,
            recommended_action=recommended_action,
        )
