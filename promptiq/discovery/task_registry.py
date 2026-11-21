"""Task Category Registry providing specialized definitions, questioning paths, and validation rules across 10 task families."""

from dataclasses import dataclass, field
from typing import Any

from promptiq.schemas.discovery import DiscoveryQuestion


@dataclass
class TaskCategoryDefinition:
    """Structured configuration defining discovery logic for a specific task family."""

    task_type: str
    display_name: str
    description: str
    stages: list[str]
    default_questions: list[DiscoveryQuestion]
    missing_info_keys: list[tuple[str, str]] = field(default_factory=list)  # (key, description)


class TaskCategoryRegistry:
    """Central registry for all PromptIQ task families supporting dynamic extension."""

    _registry: dict[str, TaskCategoryDefinition] = {}

    @classmethod
    def register(cls, definition: TaskCategoryDefinition) -> None:
        """Registers or overrides a task category definition."""
        cls._registry[definition.task_type] = definition

    @classmethod
    def get(cls, task_type: str) -> TaskCategoryDefinition | None:
        """Retrieves a task category definition by type or alias."""
        # Normalize aliases
        if task_type in cls._registry:
            return cls._registry[task_type]

        alias_map = {
            "prompt_creation": "general_prompt",
            "prompt_eval": "general_prompt",
        }
        normalized = alias_map.get(task_type, task_type)
        return cls._registry.get(normalized)

    @classmethod
    def list_all(cls) -> list[TaskCategoryDefinition]:
        """Returns all registered task category definitions."""
        return list(cls._registry.values())

    @classmethod
    def get_questions(
        cls,
        task_type: str,
        answered_keys: set[str],
        depth: str = "guided",
    ) -> list[DiscoveryQuestion]:
        """Returns un-answered discovery questions filtered by depth."""
        cat = cls.get(task_type)
        if not cat:
            return []

        unanswered = [q for q in cat.default_questions if q.id not in answered_keys]

        if depth == "quick":
            return unanswered[:1]
        elif depth == "guided":
            return unanswered[:3]
        else:  # deep
            return unanswered

    @classmethod
    def detect_missing_info(
        cls,
        task_type: str,
        answers: dict[str, Any],
        depth: str = "guided",
    ) -> list[str]:
        """Checks answers against expected high-impact fields for the task family."""
        cat = cls.get(task_type)
        if not cat:
            return []

        missing: list[str] = []
        for key, description in cat.missing_info_keys:
            if key not in answers:
                # In quick mode, only check the very first critical item
                if depth == "quick" and len(missing) >= 1:
                    break
                missing.append(description)

        return missing


# 11. Legacy / Specialized Prompt Improvement
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="prompt_improvement",
        display_name="Prompt Diagnosis & Improvement",
        description="Diagnosing existing prompt failures, removing ambiguities, and tightening output constraints.",
        stages=["diagnosis", "preservation", "refinements"],
        default_questions=[
            DiscoveryQuestion(
                id="existing_prompt",
                stage="diagnosis",
                question="Paste the current prompt you wish to improve:",
                question_type="text",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="current_failures",
                stage="diagnosis",
                question="What is failing with the current prompt?",
                question_type="multi_select",
                options=[
                    "Hallucinations or inaccurate facts",
                    "Overly verbose or conversational fluff",
                    "Ignores output format or JSON structure",
                    "Fails on edge cases or complex logic",
                    "Target environment incompatibility",
                ],
            ),
            DiscoveryQuestion(
                id="preservation_rules",
                stage="preservation",
                question="What key instructions or outputs must be strictly preserved?",
            ),
        ],
        missing_info_keys=[
            ("existing_prompt", "Original prompt text to diagnose"),
            ("current_failures", "Observed failure symptoms or regression reports"),
        ],
    )
)

# 1. Software Engineering
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="software_project",
        display_name="Software Engineering & Systems",
        description="Backend services, distributed systems, CLI tools, libraries, and APIs.",
        stages=["overview", "scope", "technical", "verification"],
        default_questions=[
            DiscoveryQuestion(
                id="problem_statement",
                stage="overview",
                question="What exact technical or business problem does this software solve?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="must_have_features",
                stage="scope",
                question="What are the essential must-have functional capabilities for this release?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="tech_stack_preference",
                stage="technical",
                question="What languages, frameworks, or databases are preferred or prohibited?",
                help_text="e.g. Python, FastAPI, SQLite / PostgreSQL; Prohibited: React, Node.js",
            ),
            DiscoveryQuestion(
                id="acceptance_criteria",
                stage="verification",
                question="What deterministic test or validation conditions define complete success?",
                help_text="e.g. All unit tests pass, zero lint warnings, deterministic CLI output",
            ),
        ],
        missing_info_keys=[
            ("problem_statement", "Core problem statement and objective"),
            ("must_have_features", "Essential must-have feature boundaries"),
            (
                "acceptance_criteria",
                "Measurable acceptance criteria / test validation conditions (Stage K)",
            ),
            ("tech_stack_preference", "Target programming language and runtime constraints"),
        ],
    )
)

# 2. Research & Investigation
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="research",
        display_name="Academic & Technical Research",
        description="Technical investigations, literature reviews, standards analysis, and competitive landscape.",
        stages=["scope", "sources", "methodology", "synthesis"],
        default_questions=[
            DiscoveryQuestion(
                id="decision_supported",
                stage="scope",
                question="What specific decision or technical architecture choice will this research support?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="source_hierarchy",
                stage="sources",
                question="What source classes are acceptable for evidence extraction?",
                question_type="multi_select",
                options=[
                    "Official provider documentation & release notes",
                    "Academic papers & peer-reviewed preprints",
                    "RFCs & formal industry specifications",
                    "Open-source repository code & issue trackers",
                ],
            ),
            DiscoveryQuestion(
                id="timeframe",
                stage="scope",
                question="What is the relevant timeframe for the research findings?",
                question_type="single_select",
                options=["Latest 30 days", "Past 6 months", "Past 1 year", "All time"],
                default_value="Past 6 months",
            ),
            DiscoveryQuestion(
                id="contradiction_handling",
                stage="methodology",
                question="How should conflicting claims between different sources be handled?",
                question_type="single_select",
                options=[
                    "Highlight contradictions explicitly in evidence ledger",
                    "Favor primary vendor documentation over secondary sources",
                    "Flag as unverified until corroborating evidence is found",
                ],
                default_value="Highlight contradictions explicitly in evidence ledger",
            ),
        ],
        missing_info_keys=[
            ("decision_supported", "Decision or hypothesis supported by research"),
            ("source_hierarchy", "Acceptable source hierarchy requirements"),
            ("timeframe", "Evidence freshness timeframe"),
        ],
    )
)

# 3. Business Strategy
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="business_strategy",
        display_name="Business Strategy & Market Planning",
        description="Market opportunity analysis, unit economics, go-to-market plans, and competitive positioning.",
        stages=["market_context", "value_prop", "monetization", "kpis"],
        default_questions=[
            DiscoveryQuestion(
                id="target_market",
                stage="market_context",
                question="Who is the primary customer segment and ideal buyer profile?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="value_proposition",
                stage="value_prop",
                question="What is the differentiated value proposition compared to incumbents?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="monetization_model",
                stage="monetization",
                question="What is the monetization or revenue model?",
                question_type="single_select",
                options=[
                    "100% Free / Open Source",
                    "SaaS Subscription",
                    "Usage-Based / Metered",
                    "Enterprise License",
                ],
                default_value="100% Free / Open Source",
            ),
            DiscoveryQuestion(
                id="strategic_kpis",
                stage="kpis",
                question="What primary key performance indicators (KPIs) measure strategic success?",
                help_text="e.g. Monthly active users, net retention, customer acquisition cost, gross margin",
            ),
        ],
        missing_info_keys=[
            ("target_market", "Target customer segment and buyer profile"),
            ("value_proposition", "Core differentiation and value proposition"),
            ("monetization_model", "Monetization and pricing structure"),
        ],
    )
)

# 4. Product Development
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="product_development",
        display_name="Product Development & PRD",
        description="Product requirements documents, user personas, journey mapping, and feature roadmaps.",
        stages=["user_personas", "core_journey", "feature_specs", "release_criteria"],
        default_questions=[
            DiscoveryQuestion(
                id="target_personas",
                stage="user_personas",
                question="Who are the primary and secondary user personas for this product?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="core_user_journey",
                stage="core_journey",
                question="What is the end-to-end user journey from initial discovery to successful outcome?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="feature_priorities",
                stage="feature_specs",
                question="What features belong in MVP (P0) versus subsequent iterations (P1/P2)?",
            ),
            DiscoveryQuestion(
                id="release_criteria",
                stage="release_criteria",
                question="What qualitative and quantitative criteria determine product launch readiness?",
            ),
        ],
        missing_info_keys=[
            ("target_personas", "Target user personas and user problem space"),
            ("core_user_journey", "End-to-end user workflow journey"),
            ("release_criteria", "Product launch readiness criteria"),
        ],
    )
)

# 5. Agent Creation
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="agent_creation",
        display_name="Autonomous AI Agent Architecture",
        description="Agent role definitions, system instructions, tool calling permissions, and escalation boundaries.",
        stages=["identity", "permissions", "safeguards", "runtime"],
        default_questions=[
            DiscoveryQuestion(
                id="agent_role",
                stage="identity",
                question="What is the agent's explicit operational role and authority scope?",
                is_required=True,
                help_text="e.g. Autonomous Code Reviewer, Security Auditor, Research Assistant",
            ),
            DiscoveryQuestion(
                id="tool_permissions",
                stage="permissions",
                question="What tool permissions and execution capabilities should the agent possess?",
                question_type="multi_select",
                options=[
                    "Read-only filesystem access",
                    "File modification (requires human approval)",
                    "Terminal/Shell command execution (requires human approval)",
                    "Web search & HTTP retrieval",
                    "MCP server tool calling",
                ],
            ),
            DiscoveryQuestion(
                id="stop_conditions",
                stage="safeguards",
                question="What are the explicit completion criteria or escalation conditions that cause the agent to pause?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="prohibited_behaviors",
                stage="safeguards",
                question="What actions or behaviors are strictly prohibited for this agent?",
                help_text="e.g. No external API calls without confirmation, no credential logging",
            ),
        ],
        missing_info_keys=[
            ("agent_role", "Operational role and authority definition"),
            ("tool_permissions", "Explicit tool permissions and safety boundaries"),
            ("stop_conditions", "Stop conditions and human escalation criteria"),
        ],
    )
)

# 6. Writing & Content
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="writing_content",
        display_name="Content Creation & Long-Form Writing",
        description="Technical essays, blog posts, whitepapers, copy, and documentation narratives.",
        stages=["objective", "audience", "tone_style", "structure"],
        default_questions=[
            DiscoveryQuestion(
                id="content_objective",
                stage="objective",
                question="What is the core takeaway or thesis the reader must understand?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="target_audience",
                stage="audience",
                question="Who is the intended reader and what is their assumed background knowledge?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="tone_and_voice",
                stage="tone_style",
                question="What style and tone should be adopted?",
                question_type="single_select",
                options=[
                    "Authoritative & Technical",
                    "Conversational & Accessible",
                    "Executive & High-Level",
                    "Academic & Rigorous",
                ],
                default_value="Authoritative & Technical",
            ),
            DiscoveryQuestion(
                id="content_format",
                stage="structure",
                question="What structural format is required?",
                question_type="single_select",
                options=[
                    "Comprehensive Guide with Subsections",
                    "Executive Summary + Deep Dive",
                    "FAQ / Q&A Style",
                    "Step-by-Step Tutorial",
                ],
                default_value="Comprehensive Guide with Subsections",
            ),
        ],
        missing_info_keys=[
            ("content_objective", "Core thesis or communication objective"),
            ("target_audience", "Target audience and technical depth"),
            ("tone_and_voice", "Desired tone, style, and voice"),
        ],
    )
)

# 7. Data Analysis
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="data_analysis",
        display_name="Data Analytics & Pipeline Engineering",
        description="Data transformation pipelines, exploratory data analysis, metric modeling, and reporting.",
        stages=["data_inputs", "analytical_scope", "transformations", "deliverables"],
        default_questions=[
            DiscoveryQuestion(
                id="data_sources",
                stage="data_inputs",
                question="What data sources, formats, and schemas will be analyzed?",
                is_required=True,
                help_text="e.g. SQLite tables, CSV files, Parquet logs, JSON streaming events",
            ),
            DiscoveryQuestion(
                id="analysis_questions",
                stage="analytical_scope",
                question="What specific analytical questions or hypotheses must be investigated?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="data_transformations",
                stage="transformations",
                question="What aggregations, statistical models, or data cleaning transformations are needed?",
            ),
            DiscoveryQuestion(
                id="output_presentation",
                stage="deliverables",
                question="How should findings be formatted?",
                question_type="single_select",
                options=[
                    "Markdown Report with Summary Tables",
                    "Clean SQL Queries + Explanations",
                    "JSON Data Contract",
                    "Python Pandas Pipeline Script",
                ],
                default_value="Markdown Report with Summary Tables",
            ),
        ],
        missing_info_keys=[
            ("data_sources", "Source data formats and schemas"),
            ("analysis_questions", "Primary analytical hypotheses or metrics"),
            ("output_presentation", "Desired reporting or data deliverable format"),
        ],
    )
)

# 8. Technical Documentation
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="technical_documentation",
        display_name="Technical Documentation & Architecture Specs",
        description="API reference documentation, system architecture records (ADRs), developer runbooks, and manuals.",
        stages=["scope", "audience_level", "standards", "deliverables"],
        default_questions=[
            DiscoveryQuestion(
                id="doc_type",
                stage="scope",
                question="What type of technical documentation is being produced?",
                question_type="single_select",
                options=[
                    "API Reference & OpenAPI Specification",
                    "Architecture Decision Record (ADR)",
                    "Operations Runbook & Deployment Guide",
                    "Developer Getting Started & Contribution Guide",
                ],
                default_value="Architecture Decision Record (ADR)",
            ),
            DiscoveryQuestion(
                id="documented_systems",
                stage="scope",
                question="What systems, services, or modules are in scope for documentation?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="code_examples_needed",
                stage="standards",
                question="Should runnable code examples, request/response payloads, or CLI commands be included?",
                question_type="single_select",
                options=[
                    "Yes - fully validated examples",
                    "Minimal illustrative snippets",
                    "No code examples required",
                ],
                default_value="Yes - fully validated examples",
            ),
        ],
        missing_info_keys=[
            ("doc_type", "Documentation type and standard"),
            ("documented_systems", "Systems or interfaces in scope"),
        ],
    )
)

# 9. Education & Learning
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="education_learning",
        display_name="Education & Curriculum Design",
        description="Interactive tutorials, technical workshops, course modules, and skill assessment frameworks.",
        stages=["learner_profile", "learning_outcomes", "pedagogy", "assessments"],
        default_questions=[
            DiscoveryQuestion(
                id="learner_profile",
                stage="learner_profile",
                question="What is the learner's prerequisite knowledge level and background?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="learning_outcomes",
                stage="learning_outcomes",
                question="What specific skills or concepts will the learner be able to demonstrate upon completion?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="pedagogical_style",
                stage="pedagogy",
                question="What instructional methodology is preferred?",
                question_type="single_select",
                options=[
                    "Hands-on project-based learning",
                    "Socratic guided discovery",
                    "Concept explanation + progressive exercises",
                    "Reference-driven deep dive",
                ],
                default_value="Hands-on project-based learning",
            ),
            DiscoveryQuestion(
                id="assessment_method",
                stage="assessments",
                question="How will learning retention and comprehension be verified?",
                help_text="e.g. Practical coding challenges, conceptual quizzes, self-evaluation checklists",
            ),
        ],
        missing_info_keys=[
            ("learner_profile", "Prerequisite knowledge and learner profile"),
            ("learning_outcomes", "Measurable learning objectives"),
            ("pedagogical_style", "Instructional methodology"),
        ],
    )
)

# 10. General Prompt Intelligence
TaskCategoryRegistry.register(
    TaskCategoryDefinition(
        task_type="general_prompt",
        display_name="General Prompt Intelligence",
        description="Custom prompt engineering, prompt improvement, system prompts, and multi-turn instructions.",
        stages=["task_details", "output_format", "constraints", "refinements"],
        default_questions=[
            DiscoveryQuestion(
                id="audience",
                stage="task_details",
                question="Who is the primary audience or consumer of this prompt's output?",
                help_text="e.g. Senior engineers, general public, executive stakeholders",
            ),
            DiscoveryQuestion(
                id="prompt_objective",
                stage="task_details",
                question="What is the exact task, capability, or role this prompt must fulfill?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="format",
                stage="output_format",
                question="What exact output format is required?",
                question_type="single_select",
                options=[
                    "Clean Markdown",
                    "Strict JSON Schema",
                    "Source Code Only",
                    "Structured Step-by-Step Report",
                ],
                default_value="Clean Markdown",
            ),
            DiscoveryQuestion(
                id="tone_and_constraints",
                stage="constraints",
                question="What tone, non-negotiable boundaries, or negative constraints must the prompt enforce?",
                help_text="e.g. Objective, zero conversational filler, reject unverified claims",
            ),
            DiscoveryQuestion(
                id="input_variables",
                stage="task_details",
                question="What dynamic input parameters or template variables will be injected at runtime?",
                help_text="e.g. {{user_code}}, {{query_text}}, {{target_language}}",
            ),
        ],
        missing_info_keys=[
            ("prompt_objective", "Primary prompt objective and task definition"),
            ("format", "Explicit output format and schema contract"),
            ("tone_and_constraints", "Negative constraints and boundary rules"),
        ],
    )
)
