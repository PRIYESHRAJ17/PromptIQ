"""Task-specific discovery question definitions delegating to TaskCategoryRegistry."""

from promptiq.discovery.task_registry import TaskCategoryRegistry
from promptiq.schemas.discovery import DiscoveryQuestion


def get_task_questions(
    task_type: str, answered_keys: set[str], depth: str = "guided"
) -> list[DiscoveryQuestion]:
    """Generates specialized follow-up questions tailored to the specific task type via TaskCategoryRegistry.

    Maintains full backwards compatibility with existing signatures.
    """
    # 1. First consult TaskCategoryRegistry
    questions = TaskCategoryRegistry.get_questions(task_type, answered_keys, depth=depth)
    if questions:
        return questions

    # 2. Fallback for legacy custom aliases if not in registry
    if task_type == "prompt_improvement":
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
        return [q for q in q_list if q.id not in answered_keys]

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
        return [q for q in q_list if q.id not in answered_keys]

    return []
