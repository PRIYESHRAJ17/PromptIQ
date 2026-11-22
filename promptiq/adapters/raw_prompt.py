"""Generic and Raw Prompt adapter."""

from typing import Any

from promptiq.adapters.base import BaseTargetAdapter
from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class RawPromptTargetAdapter(BaseTargetAdapter):
    """Compiles PPS into a clean, copy-ready prompt markdown file or prompt suite."""

    target_name: str = "raw-prompt"
    capabilities: dict[str, Any] = {
        "context_window": None,  # Output format only; no fixed host or model execution environment
        "supports_mcp": False,
        "supports_subagents": False,
        "supports_artifacts": False,
        "supports_rules_hierarchy": False,
        "supports_tool_calling": False,
        "max_output_tokens": None,
        "multimodal": False,
    }

    def compile(
        self, pps: PromptSpecSchema, output_type: OutputType
    ) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        files: dict[str, str] = {}
        warnings: list[str] = []

        reqs_text = "\n".join(
            [f"- [{r.get('id', 'REQ')}] {r.get('text')}" for r in pps.requirements]
        )
        exclusions_text = (
            "\n".join([f"- {e}" for e in pps.constraints.get("out_of_scope", [])]) or "None."
        )
        criteria_text = (
            "\n".join([f"- {c}" for c in pps.intent.success_criteria])
            or "Deliverable satisfies all requirements."
        )

        main_prompt = (
            f"# TASK DIRECTIVE\n\n"
            f"## GOAL\n{pps.intent.primary_objective}\n\n"
            f"## AUDIENCE\n{pps.intent.target_audience}\n\n"
            f"## REQUIREMENTS\n{reqs_text}\n\n"
            f"## EXCLUSIONS\n{exclusions_text}\n\n"
            f"## ACCEPTANCE CRITERIA\n{criteria_text}\n\n"
            f"## OPERATIONAL INVARIANTS\n"
            f"- Verify all code changes with tests.\n"
            f"- Do not assume missing specifications; request clarification when needed.\n"
        )

        if output_type == "prompt_suite":
            files["system_prompt.md"] = (
                f"You are a principal engineer.\n\nTask: {pps.intent.primary_objective}\n\nRequirements:\n{reqs_text}\n"
            )
            files["user_task.md"] = (
                f"Please implement the requirements according to criteria:\n{criteria_text}\n"
            )
            files["constraints.md"] = f"Exclusions:\n{exclusions_text}\n"
        else:
            files["prompt.md"] = main_prompt

        manifest = {"target": self.target_name, "type": output_type, "files": list(files.keys())}
        return manifest, files, warnings
