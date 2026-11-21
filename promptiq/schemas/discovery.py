"""Adaptive Discovery and Intake schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OutputDeliverable = Literal["prompt_only", "prompt_suite", "complete_package", "recommend"]
TargetSelectionMode = Literal["specific", "multiple", "recommend", "undecided"]
DiscoveryDepth = Literal["quick", "guided", "deep"]
TaskType = Literal[
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
    # Legacy / alias compatibility
    "prompt_creation",
    "prompt_improvement",
    "prompt_eval",
]


class InitialIntakeRequest(BaseModel):
    """The foundational intake starting point supporting goals, targets, contexts, and constraints."""

    goal: str = Field(..., min_length=5, description="What are you trying to accomplish?")
    deliverable: OutputDeliverable = Field(
        default="complete_package", description="What should PromptIQ produce?"
    )
    target: str = Field(
        default="google-antigravity",
        description="Where will you use it? (Target model/environment)",
    )
    target_mode: TargetSelectionMode = Field(
        default="specific", description="Target selection approach"
    )
    context_text: str | None = Field(default=None, description="Pasted text, prompt, or notes")
    context_urls: list[str] = Field(default_factory=list, description="Reference public URLs")
    constraints: list[str] = Field(
        default_factory=list, description="Explicit constraints or non-negotiable boundaries"
    )
    existing_files: list[dict[str, Any]] = Field(
        default_factory=list, description="Uploaded or reference files/snippets"
    )
    depth: DiscoveryDepth = Field(default="guided", description="Discovery depth")
    task_type: TaskType = Field(default="software_project", description="Category of task")


class DiscoveryQuestion(BaseModel):
    """A dynamic question presented to the user during discovery."""

    id: str
    stage: str
    question: str
    help_text: str | None = None
    why_asked: str | None = Field(
        default=None,
        description="Explanation of why this follow-up is critical for the target deliverable",
    )
    question_type: Literal["text", "single_select", "multi_select", "confirm_inferred"] = "text"
    options: list[str] = Field(default_factory=list)
    default_value: Any = None
    is_required: bool = False
    inferred_suggestion: str | None = None


class DiscoveryAnswerSubmit(BaseModel):
    """Submission of answers to active discovery questions."""

    answers: dict[str, Any] = Field(..., description="Map of question_id to answer value")


class DiscoverySessionResponse(BaseModel):
    id: str
    project_id: str
    task_type: TaskType
    depth: DiscoveryDepth
    current_stage: str
    is_completed: bool
    initial_intake: dict[str, Any]
    answers: dict[str, Any]
    extracted_facts: list[dict[str, Any]]
    identified_contradictions: list[str] = Field(default_factory=list)
    missing_high_impact_info: list[str] = Field(default_factory=list)
    next_questions: list[DiscoveryQuestion] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
