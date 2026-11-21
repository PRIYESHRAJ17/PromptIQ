"""11-Stage software project discovery definitions (Stages A through K)."""

from promptiq.schemas.discovery import DiscoveryQuestion

SOFTWARE_STAGES = [
    {
        "id": "stage_a",
        "name": "Stage A: Project Purpose",
        "questions": [
            DiscoveryQuestion(
                id="problem_statement",
                stage="stage_a",
                question="What exact problem does this software solve, and why does it matter?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="primary_users",
                stage="stage_a",
                question="Who are the primary users and what is their current manual workaround?",
            ),
        ],
    },
    {
        "id": "stage_b",
        "name": "Stage B: Users & Workflows",
        "questions": [
            DiscoveryQuestion(
                id="user_roles",
                stage="stage_b",
                question="What distinct user roles and permission levels exist?",
                question_type="multi_select",
                options=[
                    "Admin / Operator",
                    "Standard User",
                    "Viewer / Read-only",
                    "API Client / Integration",
                ],
            ),
            DiscoveryQuestion(
                id="core_user_journey",
                stage="stage_b",
                question="Walk through the core end-to-end user workflow from entry to completion.",
            ),
        ],
    },
    {
        "id": "stage_c",
        "name": "Stage C: Scope & Priorities",
        "questions": [
            DiscoveryQuestion(
                id="must_have_features",
                stage="stage_c",
                question="What are the absolute must-have features for the MVP / first useful release?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="explicit_exclusions",
                stage="stage_c",
                question="What features or requirements are explicitly OUT OF SCOPE for this release?",
            ),
        ],
    },
    {
        "id": "stage_d",
        "name": "Stage D: Functional Behavior",
        "questions": [
            DiscoveryQuestion(
                id="validation_rules",
                stage="stage_d",
                question="What critical business rules, validations, and edge cases must be handled?",
            ),
            DiscoveryQuestion(
                id="error_handling",
                stage="stage_d",
                question="How should system errors and failure states be reported to callers?",
            ),
        ],
    },
    {
        "id": "stage_e",
        "name": "Stage E: UI/UX Specifications",
        "questions": [
            DiscoveryQuestion(
                id="surfaces_required",
                stage="stage_e",
                question="What target surfaces are planned for the future application?",
                question_type="multi_select",
                options=["Web Workspace", "Mobile Companion", "CLI / Terminal", "Desktop App"],
            ),
            DiscoveryQuestion(
                id="visual_direction",
                stage="stage_e",
                question="Describe the required visual direction, density, accessibility (WCAG), and theme behavior (light/dark/system). (Note: Captured as specifications only; frontend implementation is separate).",
            ),
        ],
    },
    {
        "id": "stage_f",
        "name": "Stage F: Data & Integrations",
        "questions": [
            DiscoveryQuestion(
                id="core_entities",
                stage="stage_f",
                question="What core data entities must be modeled and stored?",
            ),
            DiscoveryQuestion(
                id="external_integrations",
                stage="stage_f",
                question="What external APIs, databases, or third-party services are required?",
            ),
        ],
    },
    {
        "id": "stage_g",
        "name": "Stage G: Technical Direction",
        "questions": [
            DiscoveryQuestion(
                id="tech_stack_preference",
                stage="stage_g",
                question="What backend languages, frameworks, or databases are preferred or required?",
                help_text="e.g. Python, FastAPI, PostgreSQL, SQLite",
            ),
            DiscoveryQuestion(
                id="architecture_pattern",
                stage="stage_g",
                question="What architectural pattern should be adopted?",
                question_type="single_select",
                options=[
                    "Modular Monolith",
                    "Microservices",
                    "Event-Driven",
                    "Serverless Functions",
                ],
                default_value="Modular Monolith",
            ),
        ],
    },
    {
        "id": "stage_h",
        "name": "Stage H: AI & Automation",
        "questions": [
            DiscoveryQuestion(
                id="ai_capabilities",
                stage="stage_h",
                question="What role does AI or automated inference play in the application?",
            ),
            DiscoveryQuestion(
                id="prohibited_ai_actions",
                stage="stage_h",
                question="What automated actions are strictly prohibited without human-in-the-loop sign-off?",
            ),
        ],
    },
    {
        "id": "stage_i",
        "name": "Stage I: Security & Privacy",
        "questions": [
            DiscoveryQuestion(
                id="sensitive_data_classes",
                stage="stage_i",
                question="What sensitive data (e.g. credentials, tokens, PII) requires special encryption or redaction?",
            ),
            DiscoveryQuestion(
                id="auth_requirements",
                stage="stage_i",
                question="What authentication and tenant isolation guarantees are required?",
            ),
        ],
    },
    {
        "id": "stage_j",
        "name": "Stage J: Research & Market Context",
        "questions": [
            DiscoveryQuestion(
                id="alternatives_and_standards",
                stage="stage_j",
                question="What existing alternatives, competitor tools, or technical standards should be referenced?",
            ),
        ],
    },
    {
        "id": "stage_k",
        "name": "Stage K: Delivery & Acceptance",
        "questions": [
            DiscoveryQuestion(
                id="acceptance_criteria",
                stage="stage_k",
                question="What measurable acceptance tests determine that the project is successfully completed?",
                is_required=True,
            ),
        ],
    },
]


def get_software_stage_questions(
    current_stage_id: str, answered_keys: set[str]
) -> list[DiscoveryQuestion]:
    """Returns questions for the active software stage, excluding already answered questions."""
    for stage in SOFTWARE_STAGES:
        if stage["id"] == current_stage_id:
            return [q for q in stage["questions"] if q.id not in answered_keys]
    return []
