"""Tests for TaskCategoryRegistry and the 10 task families."""

from promptiq.discovery.task_registry import TaskCategoryDefinition, TaskCategoryRegistry
from promptiq.schemas.discovery import DiscoveryQuestion


def test_ten_task_families_registered():
    """Verifies that all 10 core task families are registered and have valid structures."""
    core_families = [
        "software_project",
        "research",
        "business_strategy",
        "product_development",
        "agent_creation",
        "writing_content",
        "data_analysis",
        "technical_documentation",
        "education_learning",
        "general_prompt",
    ]

    for family in core_families:
        cat = TaskCategoryRegistry.get(family)
        assert cat is not None, f"Family {family} must be registered"
        assert cat.task_type == family
        assert len(cat.stages) >= 2, f"Family {family} must define multiple stages"
        assert len(cat.default_questions) >= 3, f"Family {family} must provide default questions"
        assert len(cat.missing_info_keys) >= 2, f"Family {family} must define missing info criteria"


def test_task_registry_depth_filtering():
    """Verifies that discovery depth controls question quantity without re-asking answered questions."""
    # Quick mode: 1 question
    quick_q = TaskCategoryRegistry.get_questions(
        "software_project", answered_keys=set(), depth="quick"
    )
    assert len(quick_q) == 1

    # Guided mode: at most 3 questions
    guided_q = TaskCategoryRegistry.get_questions(
        "software_project", answered_keys=set(), depth="guided"
    )
    assert len(guided_q) <= 3

    # Deep mode: full question set
    deep_q = TaskCategoryRegistry.get_questions(
        "software_project", answered_keys=set(), depth="deep"
    )
    assert len(deep_q) >= 4

    # Anti-fatigue check: answered questions are omitted
    answered = {"problem_statement"}
    filtered_q = TaskCategoryRegistry.get_questions(
        "software_project", answered_keys=answered, depth="deep"
    )
    assert not any(q.id == "problem_statement" for q in filtered_q)


def test_missing_info_detection():
    """Verifies missing info detection across task types."""
    answers = {"target_market": "B2B SaaS companies"}
    missing = TaskCategoryRegistry.detect_missing_info("business_strategy", answers, depth="guided")
    assert any("differentiation" in m.lower() or "value proposition" in m.lower() for m in missing)

    complete_answers = {
        "target_market": "B2B SaaS",
        "value_proposition": "Self-hosted prompt intelligence",
        "monetization_model": "100% Free / Open Source",
    }
    missing_none = TaskCategoryRegistry.detect_missing_info(
        "business_strategy", complete_answers, depth="guided"
    )
    assert len(missing_none) == 0


def test_custom_category_registration():
    """Verifies dynamic runtime registration of new task families."""
    custom = TaskCategoryDefinition(
        task_type="robotics_control",
        display_name="Robotics & Motion Control",
        description="Kinematics, trajectory planning, and actuator interfaces.",
        stages=["hardware", "kinematics", "safety"],
        default_questions=[
            DiscoveryQuestion(
                id="actuator_type",
                stage="hardware",
                question="What motor controllers or actuators are targeted?",
            )
        ],
        missing_info_keys=[("actuator_type", "Actuator and hardware specification")],
    )
    TaskCategoryRegistry.register(custom)

    retrieved = TaskCategoryRegistry.get("robotics_control")
    assert retrieved is not None
    assert retrieved.display_name == "Robotics & Motion Control"
    questions = TaskCategoryRegistry.get_questions("robotics_control", set())
    assert len(questions) == 1
    assert questions[0].id == "actuator_type"
