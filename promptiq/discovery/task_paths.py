"""Task-specific discovery question definitions."""

from promptiq.schemas.discovery import DiscoveryQuestion


def get_task_questions(task_type: str, answered_keys: set[str]) -> list[DiscoveryQuestion]:
    """Generates specialized follow-up questions tailored to the specific task type."""
    questions: list[DiscoveryQuestion] = []

    if task_type == "prompt_creation":
        q_list = [
            DiscoveryQuestion(
                id="audience",
                stage="task_details",
                question="Who is the primary audience or consumer of this prompt's output?",
                help_text="e.g. Senior engineers, general public, executive stakeholders",
            ),
            DiscoveryQuestion(
                id="format",
                stage="task_details",
                question="What exact output format is required?",
                question_type="single_select",
                options=["Clean Markdown", "Strict JSON Schema", "Code snippet only", "Step-by-step report"],
                default_value="Clean Markdown",
            ),
            DiscoveryQuestion(
                id="tone_and_constraints",
                stage="task_details",
                question="What tone, constraints, or explicit exclusions must the model respect?",
                help_text="e.g. Objective, concise, no conversational filler, adhere to standard X",
            ),
        ]
    elif task_type == "prompt_improvement":
        q_list = [
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
                stage="diagnosis",
                question="What key instructions or outputs must be strictly preserved?",
            ),
        ]
    elif task_type == "research":
        q_list = [
            DiscoveryQuestion(
                id="decision_supported",
                stage="scope",
                question="What specific technical or product decision will this research support?",
            ),
            DiscoveryQuestion(
                id="source_hierarchy",
                stage="scope",
                question="What source classes do you require?",
                question_type="multi_select",
                options=[
                    "Official provider documentation & release notes",
                    "Academic papers & arXiv preprints",
                    "Open-source repository code & GitHub issues",
                    "Industry standards & RFCs",
                ],
            ),
            DiscoveryQuestion(
                id="timeframe",
                stage="scope",
                question="What is the relevant timeframe for the research evidence?",
                question_type="single_select",
                options=["Latest 30 days", "Past 6 months", "Past 1 year", "All time"],
                default_value="Past 6 months",
            ),
        ]
    elif task_type == "agent_creation":
        q_list = [
            DiscoveryQuestion(
                id="agent_role",
                stage="spec",
                question="What is the agent's primary role and operational identity?",
                help_text="e.g. Autonomous Code Reviewer, Security Auditor, Research Assistant",
            ),
            DiscoveryQuestion(
                id="tool_permissions",
                stage="spec",
                question="What tool permissions should the agent possess?",
                question_type="multi_select",
                options=[
                    "Read-only filesystem access",
                    "File modification (requires approval)",
                    "Terminal/Shell command execution (requires approval)",
                    "Web search & HTTP retrieval",
                    "MCP server tool calling",
                ],
            ),
            DiscoveryQuestion(
                id="stop_conditions",
                stage="spec",
                question="What are the explicit completion criteria or escalation conditions?",
            ),
        ]
    elif task_type == "prompt_eval":
        q_list = [
            DiscoveryQuestion(
                id="candidate_prompts",
                stage="setup",
                question="Describe the prompt variants you wish to evaluate:",
            ),
            DiscoveryQuestion(
                id="assertions",
                stage="setup",
                question="What fixed assertions should define a passing test run?",
                help_text="e.g. Output contains valid JSON, covers all 5 required sections, passes latency ceiling",
            ),
        ]
    elif task_type == "software_project":
        q_list = [
            DiscoveryQuestion(
                id="problem_statement",
                stage="overview",
                question="What exact problem does this software solve?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="must_have_features",
                stage="scope",
                question="What are the essential must-have features for the initial release?",
                is_required=True,
            ),
            DiscoveryQuestion(
                id="tech_stack_preference",
                stage="technical",
                question="What languages, frameworks, or databases are preferred?",
                help_text="e.g. Python, FastAPI, PostgreSQL",
            ),
        ]
    else:
        q_list = []

    # Filter out already answered questions to prevent user fatigue
    for q in q_list:
        if q.id not in answered_keys:
            questions.append(q)

    return questions
