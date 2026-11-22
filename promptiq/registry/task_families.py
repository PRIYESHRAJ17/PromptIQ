"""Task Family Specialization Registry for all 10 PromptIQ Task Families."""

from typing import Any

from pydantic import BaseModel, Field


class TaskFamilySpecification(BaseModel):
    id: str
    display_name: str
    description: str
    preferred_target: str
    discovery_profile: str
    planning_rules: list[str] = Field(default_factory=list)
    pps_validation_rules: list[str] = Field(default_factory=list)
    compiler_guidance: dict[str, Any] = Field(default_factory=dict)
    autopsy_emphasis: list[str] = Field(default_factory=list)
    autopsy_ignored_categories: list[str] = Field(default_factory=list)
    test_lab_methodology: str
    acceptance_criteria: list[str] = Field(default_factory=list)


TASK_FAMILIES: dict[str, TaskFamilySpecification] = {
    "software_engineering": TaskFamilySpecification(
        id="software_engineering",
        display_name="Software Engineering",
        description="Architecture, repository context, APIs, database migrations, security boundaries, and tests.",
        preferred_target="raw_prompt",
        discovery_profile="technical",
        planning_rules=[
            "Enforce modular architecture and multi-tenant isolation",
            "Validate database migrations and relational constraints",
            "Assert zero website frontend UI components",
        ],
        pps_validation_rules=[
            "Must define technical direction and prohibited stack",
            "Must provide deterministic verification methods for P0 requirements",
        ],
        compiler_guidance={
            "include_architecture_pattern": True,
            "include_schema_definitions": True,
            "enforce_strict_error_handling": True,
        },
        autopsy_emphasis=[
            "unsafe_permissions",
            "missing_error_handling",
            "missing_testability",
            "tool_misuse",
            "contradictions",
        ],
        autopsy_ignored_categories=[],
        test_lab_methodology="deterministic_assertions_and_schema_validation",
        acceptance_criteria=[
            "Zero prohibited frontend libraries or UI tags",
            "All functional endpoints have documented error contracts",
            "Deterministic test cases pass with score >= 0.85",
        ],
    ),
    "research_intelligence": TaskFamilySpecification(
        id="research_intelligence",
        display_name="Research Intelligence",
        description="Literature search, source evaluation, evidence graphs, citation offsets, and contradiction analysis.",
        preferred_target="raw_prompt",
        discovery_profile="research",
        planning_rules=[
            "Decompose research question into verifiable sub-hypotheses",
            "Require source hierarchy (primary/official docs > peer-reviewed > industry)",
            "Track exact character offsets for evidence excerpts",
        ],
        pps_validation_rules=[
            "Must define freshness requirements and source reliability thresholds",
            "Must specify citation and provenance ledger tracking",
        ],
        compiler_guidance={
            "structure_as_evidence_brief": True,
            "require_contradiction_analysis": True,
        },
        autopsy_emphasis=[
            "unsupported_claims",
            "vagueness",
            "incomplete_context",
        ],
        autopsy_ignored_categories=["missing_output_schema"],
        test_lab_methodology="citation_verification_and_evidence_grounding",
        acceptance_criteria=[
            "100% of material claims reference valid evidence IDs",
            "Clear distinction between live external search and simulated fallback",
        ],
    ),
    "ai_agent_development": TaskFamilySpecification(
        id="ai_agent_development",
        display_name="AI Agent Development",
        description="Autonomous agent definitions, tool permissions, delegation loops, memory, and safety boundaries.",
        preferred_target="antigravity",
        discovery_profile="agentic",
        planning_rules=[
            "Define strict tool permissions and read-only vs mutating boundaries",
            "Specify bounded retries to prevent runaway self-reflection loops",
            "Configure fail-closed security for unapproved actions",
        ],
        pps_validation_rules=[
            "Must define tools, allowed operations, and human escalation gates",
            "Must provide stopping conditions for agent loops",
        ],
        compiler_guidance={
            "generate_antigravity_agents_md": True,
            "target_format": "AGENTS.md",
        },
        autopsy_emphasis=[
            "excessive_agency",
            "unsafe_permissions",
            "missing_stop_conditions",
            "prompt_injection",
            "system_instruction_extraction",
        ],
        autopsy_ignored_categories=[],
        test_lab_methodology="permission_boundary_audit_and_adversarial_injection",
        acceptance_criteria=[
            "Zero unconstrained mutating permissions granted",
            "Explicit stopping conditions present",
            "Passes prompt injection and roleplay jailbreak tests",
        ],
    ),
    "business_strategy": TaskFamilySpecification(
        id="business_strategy",
        display_name="Business Strategy",
        description="Market assumptions, target customer segments, unit economics, risks, and execution milestones.",
        preferred_target="raw_prompt",
        discovery_profile="business",
        planning_rules=[
            "Identify and tag unverified market assumptions",
            "Analyze competitive positioning and defensibility",
            "Define measurable milestones and risk mitigation",
        ],
        pps_validation_rules=[
            "Must define target audience and success metrics",
        ],
        compiler_guidance={
            "structure_as_executive_brief": True,
        },
        autopsy_emphasis=[
            "unsupported_claims",
            "ambiguity",
            "vagueness",
        ],
        autopsy_ignored_categories=["missing_output_schema", "tool_misuse"],
        test_lab_methodology="assumption_traceability_and_metric_grounding",
        acceptance_criteria=[
            "Assumptions clearly segregated from verified market facts",
            "Execution milestones have assigned risk levels and owners",
        ],
    ),
    "prompt_improvement": TaskFamilySpecification(
        id="prompt_improvement",
        display_name="Prompt Improvement",
        description="Intent preservation, precision enhancement, constraint hardening, and safety verification.",
        preferred_target="raw_prompt",
        discovery_profile="quick",
        planning_rules=[
            "Preserve user's core intent while eliminating ambiguity",
            "Inject explicit negative constraints and stopping conditions",
            "Enforce concise, token-efficient prompt structures",
        ],
        pps_validation_rules=[
            "Must reference original prompt text and target model capabilities",
        ],
        compiler_guidance={
            "optimize_density": True,
            "strip_unnecessary_filler": True,
        },
        autopsy_emphasis=[
            "ambiguity",
            "vagueness",
            "missing_negative_constraints",
            "unnecessary_complexity",
            "excessive_context",
        ],
        autopsy_ignored_categories=[],
        test_lab_methodology="comparative_autopsy_and_token_efficiency",
        acceptance_criteria=[
            "Zero open critical or high autopsy findings on refined prompt",
            "Refined prompt achieves higher benchmark score than original",
        ],
    ),
    "product_development": TaskFamilySpecification(
        id="product_development",
        display_name="Product Development",
        description="Product architecture, user journeys, functional specs, MVP scoping, and PRDs.",
        preferred_target="cursor",
        discovery_profile="guided",
        planning_rules=[
            "Translate business objectives into detailed user journeys",
            "Scope MVP features vs subsequent milestone capabilities",
            "Define acceptance criteria per user persona",
        ],
        pps_validation_rules=[
            "Must define user personas and functional requirement priorities",
        ],
        compiler_guidance={
            "generate_cursor_rules": True,
            "target_format": ".cursorrules",
        },
        autopsy_emphasis=[
            "missing_requirements",
            "incomplete_context",
            "contradictions",
        ],
        autopsy_ignored_categories=["tool_misuse"],
        test_lab_methodology="persona_journey_coverage_and_madr_validation",
        acceptance_criteria=[
            "All core user journeys have concrete acceptance criteria",
            "PRD contains zero ambiguous feature requirements",
        ],
    ),
    "writing_content": TaskFamilySpecification(
        id="writing_content",
        display_name="Writing & Content",
        description="Audience adaptation, tone, style rubrics, editorial structure, and factual citations.",
        preferred_target="raw_prompt",
        discovery_profile="creative",
        planning_rules=[
            "Define authoritative voice and stylistic tone",
            "Preserve author intent and narrative pacing",
            "Enforce factual grounding where factual claims are made",
        ],
        pps_validation_rules=[
            "Must specify target reader persona and tone constraints",
        ],
        compiler_guidance={
            "structure_for_clarity_and_flow": True,
        },
        autopsy_emphasis=[
            "ambiguity",
            "vagueness",
            "unnecessary_complexity",
        ],
        autopsy_ignored_categories=["missing_output_schema", "tool_misuse", "unsafe_permissions"],
        test_lab_methodology="readability_rubric_and_style_adherence",
        acceptance_criteria=[
            "Tone adheres to specified audience level",
            "Structure conforms to editorial guidelines",
        ],
    ),
    "data_analysis": TaskFamilySpecification(
        id="data_analysis",
        display_name="Data Analysis",
        description="Dataset schemas, SQL queries, statistical validation, missing value handling, and data integrity.",
        preferred_target="codex",
        discovery_profile="technical",
        planning_rules=[
            "Verify table schemas, data types, and primary keys",
            "Enforce reproducible SQL and statistical methodologies",
            "Prohibit hallucination of unprovided data",
        ],
        pps_validation_rules=[
            "Must define input data schemas and expected output structure",
        ],
        compiler_guidance={
            "generate_codex_instructions": True,
            "target_format": "CODEX.md",
        },
        autopsy_emphasis=[
            "unsupported_claims",
            "missing_error_handling",
            "missing_output_schema",
            "missing_testability",
        ],
        autopsy_ignored_categories=[],
        test_lab_methodology="schema_validation_and_query_soundness",
        acceptance_criteria=[
            "SQL queries parse cleanly with valid syntax",
            "Statistical limitations and missing values explicitly handled",
        ],
    ),
    "technical_documentation": TaskFamilySpecification(
        id="technical_documentation",
        display_name="Technical Documentation",
        description="Architectural decision records (MADR), API references, runbooks, and Markdown lint compliance.",
        preferred_target="gemini",
        discovery_profile="technical",
        planning_rules=[
            "Conform to MADR 3.0 architectural decision records",
            "Validate code snippets and configuration blocks",
            "Assert strict Markdown heading hierarchy",
        ],
        pps_validation_rules=[
            "Must specify target technical audience and version compatibility",
        ],
        compiler_guidance={
            "generate_gemini_cli_rules": True,
            "target_format": "GEMINI.md",
        },
        autopsy_emphasis=[
            "incomplete_context",
            "missing_testability",
            "contradictions",
        ],
        autopsy_ignored_categories=["tool_misuse"],
        test_lab_methodology="markdown_lint_and_reference_consistency",
        acceptance_criteria=[
            "Conforms to MADR 3.0 or OpenAPI 3.1 standards",
            "Zero broken internal references or formatting violations",
        ],
    ),
    "education_learning": TaskFamilySpecification(
        id="education_learning",
        display_name="Education & Learning",
        description="Curriculum design, pedagogical progression, prerequisite mapping, and self-assessment checks.",
        preferred_target="claude",
        discovery_profile="guided",
        planning_rules=[
            "Structure learning objectives using Bloom's Taxonomy",
            "Map prerequisites and progressive difficulty steps",
            "Include self-assessment questions and practical exercises",
        ],
        pps_validation_rules=[
            "Must specify learner baseline and target learning outcomes",
        ],
        compiler_guidance={
            "generate_claude_code_instructions": True,
            "target_format": "CLAUDE.md",
        },
        autopsy_emphasis=[
            "incomplete_context",
            "ambiguity",
            "vagueness",
            "missing_testability",
        ],
        autopsy_ignored_categories=["unsafe_permissions", "tool_misuse"],
        test_lab_methodology="pedagogical_coherence_and_assessment_coverage",
        acceptance_criteria=[
            "Each module has measurable learning outcomes",
            "Self-assessment checkpoints verify prerequisite understanding",
        ],
    ),
}


class TaskFamilyRegistry:
    """Provides centralized lookup and enforcement for all 10 PromptIQ task families."""

    @classmethod
    def get_family(cls, task_type: str) -> TaskFamilySpecification:
        """Retrieves specification for task family or falls back to software_engineering."""
        norm_type = task_type.lower().replace("-", "_").replace(" ", "_")
        return TASK_FAMILIES.get(norm_type, TASK_FAMILIES["software_engineering"])

    @classmethod
    def list_families(cls) -> list[TaskFamilySpecification]:
        """Lists all registered task families."""
        return list(TASK_FAMILIES.values())
