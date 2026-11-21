"""Prompt Package schemas for compilation and export."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OutputType = Literal["prompt_only", "prompt_suite", "complete_package"]


class PackageCompileRequest(BaseModel):
    """Request to compile a Project Constitution into a target-native package."""

    target_environment: str = Field(
        default="google-antigravity",
        description="Target host (google-antigravity, claude-code, cursor, openai-codex, gemini-cli, raw-prompt)",
    )
    output_type: OutputType = Field(
        default="complete_package",
        description="Delivery granularity: prompt_only, prompt_suite, complete_package",
    )
    custom_instructions: str | None = None


class PromptPackageResponse(BaseModel):
    id: str
    project_id: str
    spec_id: str
    target_environment: str
    output_type: str
    manifest: dict[str, Any]
    files: dict[str, str]  # file_path -> content
    warnings: list[str]
    is_validated: bool
    validation_result: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PackageExportResponse(BaseModel):
    package_id: str
    target_environment: str
    file_count: int
    manifest: dict[str, Any]
    download_url: str | None = None
    files: dict[str, str]
