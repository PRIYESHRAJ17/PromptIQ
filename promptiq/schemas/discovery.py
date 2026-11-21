"""Adaptive Discovery and Intake schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OutputDeliverable = Literal["prompt_only", "prompt_suite", "complete_package", "recommend"]
TargetSelectionMode = Literal["specific", "multiple", "recommend", "undecided"]
DiscoveryDepth = Literal["quick", "guided", "deep"]
TaskType = Literal[
    "prompt_creation",
    "prompt_improvement",
    "research",
    "software_project",
    "agent_creation",
    "prompt_eval",
]


class InitialIntakeRequest(BaseModel):
    """The foundational 4-input intake starting point."""

    goal: str = Field(..., min_length=5, description="What are you trying to accomplish?")
    deliverable: OutputDeliverable = Field(default="complete_package", description="What should PromptIQ produce?")
    target: str = Field(default="google-antigravity", description="Where will you use it? (Target model/environment)")
    target_mode: TargetSelectionMode = Field(default="specific", description="Target selection approach")
    context_text: str | None = Field(default=None, description="Pasted text, prompt, or notes")
    context_urls: list[str] = Field(default_factory=list, description="Reference public URLs")
    depth: DiscoveryDepth = Field(default="guided", description="Discovery depth")
    task_type: TaskType = Field(default="software_project", description="Category of task")


class DiscoveryQuestion(BaseModel):
    """A dynamic question presented to the user during discovery."""

    id: str
    stage: str
    question: str
    help_text: str | None = None
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
    next_questions: list[DiscoveryQuestion] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
