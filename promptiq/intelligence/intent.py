"""PromptIQ Advanced Intent Reasoning and Uncertainty Engine."""

import re
from enum import StrEnum

from pydantic import BaseModel, Field


class RequirementProvenance(StrEnum):
    EXPLICIT_PROVIDED = "explicit_provided"
    STRONGLY_IMPLIED = "strongly_implied"
    REASONABLE_ASSUMPTION = "reasonable_assumption"
    UNVERIFIED_ASSUMPTION = "unverified_assumption"
    UNKNOWN = "unknown"


class ImpactLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IntentAnalysisItem(BaseModel):
    id: str
    description: str
    provenance: RequirementProvenance
    impact: ImpactLevel
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_rationale: str
    source_reference: str | None = None
    affects_architecture: bool = False
    needs_clarification: bool = False


class IntentProfile(BaseModel):
    primary_objective: str
    secondary_objectives: list[str] = Field(default_factory=list)
    expected_deliverables: list[str] = Field(default_factory=list)
    target_audience: str = "general"
    task_complexity: str = "medium"  # low, medium, high, extreme
    technical_constraints: list[str] = Field(default_factory=list)
    business_constraints: list[str] = Field(default_factory=list)
    time_constraints: list[str] = Field(default_factory=list)
    explicit_prohibitions: list[str] = Field(default_factory=list)
    implied_requirements: list[IntentAnalysisItem] = Field(default_factory=list)
    assumptions: list[IntentAnalysisItem] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    conflicting_instructions: list[str] = Field(default_factory=list)
    success_conditions: list[str] = Field(default_factory=list)
    high_impact_unknowns: list[IntentAnalysisItem] = Field(default_factory=list)
    information_sufficiency_score: float = Field(default=0.5, ge=0.0, le=1.0)


class IntentReasoningEngine:
    """Performs deep intent extraction, requirement provenance tagging, and uncertainty analysis."""

    @classmethod
    def analyze_intent(
        cls,
        goal: str,
        context_text: str | None = None,
        constraints: list[str] | None = None,
        task_type: str = "software_engineering",
    ) -> IntentProfile:
        """Analyzes user goal, context, and constraints to build a rich IntentProfile."""
        text = f"{goal} {context_text or ''} {' '.join(constraints or [])}".strip()
        lower_text = text.lower()

        # 1. Primary & Secondary Objectives
        sentences = [s.strip() for s in re.split(r"[.\n;]+", goal) if s.strip()]
        primary_objective = sentences[0] if sentences else goal
        secondary_objectives = sentences[1:5] if len(sentences) > 1 else []

        # 2. Explicit Prohibitions
        prohibitions = []
        if constraints:
            for c in constraints:
                c_lower = c.lower()
                if any(w in c_lower for w in ["no ", "never", "do not", "strictly no", "prohibit"]):
                    prohibitions.append(c)

        # Detect built-in invariants
        if any(w in lower_text for w in ["no frontend", "backend only", "no ui", "api only"]):
            if "Strictly no website frontend" not in prohibitions:
                prohibitions.append("Strictly no website frontend")

        if any(w in lower_text for w in ["free", "zero cost", "zero price", "₹0"]):
            if "Strictly zero price to users forever (no paid routes or BYOK)" not in prohibitions:
                prohibitions.append("Strictly zero price to users forever (no paid routes or BYOK)")

        # 3. Expected Deliverables
        deliverables = []
        if any(w in lower_text for w in ["api", "rest", "endpoint", "backend"]):
            deliverables.append("REST API Endpoints")
        if any(w in lower_text for w in ["database", "schema", "postgres", "sql"]):
            deliverables.append("Database Schema & Migrations")
        if any(w in lower_text for w in ["prompt", "instructions", "system prompt", "agent"]):
            deliverables.append("Structured Prompt Package")
        if any(w in lower_text for w in ["test", "tests", "eval", "benchmark"]):
            deliverables.append("Verification Test Suite")
        if not deliverables:
            deliverables.append("Operational Specification & Deliverable Artifacts")

        # 4. Complexity Analysis
        word_count = len(text.split())
        constraint_count = len(constraints or [])
        if (
            word_count > 150
            or constraint_count >= 5
            or "distributed" in lower_text
            or "multi-tenant" in lower_text
        ):
            task_complexity = "high"
        elif word_count > 60 or constraint_count >= 2:
            task_complexity = "medium"
        else:
            task_complexity = "low"

        # 5. Implied Requirements & Assumptions
        implied_reqs: list[IntentAnalysisItem] = []
        assumptions: list[IntentAnalysisItem] = []
        high_impact_unknowns: list[IntentAnalysisItem] = []

        # Multi-tenancy implication
        if any(w in lower_text for w in ["organization", "tenant", "workspace", "saas", "team"]):
            implied_reqs.append(
                IntentAnalysisItem(
                    id="IMP-001",
                    description="Multi-tenant row-level authorization and workspace isolation boundaries required",
                    provenance=RequirementProvenance.STRONGLY_IMPLIED,
                    impact=ImpactLevel.CRITICAL,
                    confidence=0.92,
                    confidence_rationale="Explicit mention of organizations/workspaces implies strict isolation",
                    affects_architecture=True,
                    needs_clarification=False,
                )
            )

        # Audit history implication
        if any(w in lower_text for w in ["audit", "history", "compliance", "log", "trace"]):
            implied_reqs.append(
                IntentAnalysisItem(
                    id="IMP-002",
                    description="Immutable audit logging for sensitive state transitions",
                    provenance=RequirementProvenance.STRONGLY_IMPLIED,
                    impact=ImpactLevel.HIGH,
                    confidence=0.88,
                    confidence_rationale="Compliance/audit directives necessitate immutable audit trails",
                    affects_architecture=True,
                    needs_clarification=False,
                )
            )

        # Authentication assumption
        if any(w in lower_text for w in ["user", "login", "auth", "donor", "customer"]):
            if "jwt" in lower_text or "token" in lower_text:
                assumptions.append(
                    IntentAnalysisItem(
                        id="ASM-001",
                        description="JWT bearer token authentication with server-side revocation",
                        provenance=RequirementProvenance.REASONABLE_ASSUMPTION,
                        impact=ImpactLevel.HIGH,
                        confidence=0.85,
                        confidence_rationale="JWT/token mentioned in context text; standard for stateless API",
                        affects_architecture=True,
                        needs_clarification=False,
                    )
                )
            else:
                high_impact_unknowns.append(
                    IntentAnalysisItem(
                        id="UNK-001",
                        description="Authentication mechanism unspecified (JWT vs Session vs OAuth2)",
                        provenance=RequirementProvenance.UNKNOWN,
                        impact=ImpactLevel.HIGH,
                        confidence=0.40,
                        confidence_rationale="User roles present but auth scheme not specified",
                        affects_architecture=True,
                        needs_clarification=True,
                    )
                )

        # Technical Constraints
        tech_constraints = []
        if "sqlite" in lower_text:
            tech_constraints.append("SQLite embedded database")
        if "postgres" in lower_text or "postgresql" in lower_text:
            tech_constraints.append("PostgreSQL database")
        if "fastapi" in lower_text:
            tech_constraints.append("FastAPI framework")
        if "python 3.13" in lower_text or "python" in lower_text:
            tech_constraints.append("Python 3.13 runtime")

        # 6. Ambiguities & Conflicting Instructions
        ambiguities = []
        conflicts = []
        if "realtime" in lower_text and not any(
            w in lower_text for w in ["sse", "websocket", "polling"]
        ):
            ambiguities.append(
                "Real-time communication requested without specifying transport (SSE vs WebSocket)"
            )

        # Contradiction checks
        no_frontend = any(
            "no frontend" in p.lower() or "backend only" in p.lower() for p in prohibitions
        )
        if no_frontend and any(
            w in lower_text for w in ["react", "next.js", "html", "css", "tailwind"]
        ):
            conflicts.append(
                "Strict no-frontend prohibition conflicts with mention of web UI technologies"
            )

        # 7. Success Conditions
        success_conditions = [
            f"Observable fulfillment of primary goal: {primary_objective[:80]}",
            "Zero unhandled runtime exceptions during workflow execution",
            "100% adherence to explicit prohibitions and architectural boundaries",
        ]

        # 8. Information Sufficiency Calculation
        # Base sufficiency from inputs
        score = 0.3
        if len(sentences) >= 2:
            score += 0.2
        if constraints and len(constraints) >= 2:
            score += 0.2
        if tech_constraints:
            score += 0.15
        if not high_impact_unknowns:
            score += 0.15
        else:
            score -= 0.1 * len(high_impact_unknowns)

        score = max(0.1, min(0.98, score))

        return IntentProfile(
            primary_objective=primary_objective,
            secondary_objectives=secondary_objectives,
            expected_deliverables=deliverables,
            target_audience="Engineers and Domain Operators",
            task_complexity=task_complexity,
            technical_constraints=tech_constraints,
            business_constraints=constraints or [],
            time_constraints=[],
            explicit_prohibitions=prohibitions,
            implied_requirements=implied_reqs,
            assumptions=assumptions,
            ambiguities=ambiguities,
            conflicting_instructions=conflicts,
            success_conditions=success_conditions,
            high_impact_unknowns=high_impact_unknowns,
            information_sufficiency_score=score,
        )
