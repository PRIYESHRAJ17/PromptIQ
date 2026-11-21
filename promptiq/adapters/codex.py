"""OpenAI Codex / ChatGPT Plugin adapter."""

import json
from typing import Any

from promptiq.adapters.base import BaseTargetAdapter
from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class CodexTargetAdapter(BaseTargetAdapter):
    """Compiles PPS into OpenAI plugin packaging and instructions."""

    target_name: str = "openai-codex"

    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        files: dict[str, str] = {}
        warnings: list[str] = []

        reqs_text = "\n".join([f"- {r.get('id')}: {r.get('text')}" for r in pps.requirements])

        plugin_json = {
            "schema_version": "v1",
            "name_for_model": "promptiq_executor",
            "name_for_human": "PromptIQ Execution Adapter",
            "description_for_model": f"Instructions and tools for: {pps.intent.primary_objective}",
            "description_for_human": pps.intent.primary_objective,
            "auth": {"type": "none"},
            "api": {"type": "openapi", "url": "/openapi.yaml"},
        }

        files[".well-known/ai-plugin.json"] = json.dumps(plugin_json, indent=2)
        files["instructions.md"] = f"# CODEX INSTRUCTIONS\n\nObjective: {pps.intent.primary_objective}\n\nRequirements:\n{reqs_text}\n"

        if output_type == "complete_package":
            files["openapi.yaml"] = (
                "openapi: 3.0.1\n"
                "info:\n"
                "  title: PromptIQ Tool Contract\n"
                "  version: 1.0.0\n"
                "paths: {}\n"
            )
            files["README.md"] = f"# OpenAI Codex Package\n\nGoal: {pps.intent.primary_objective}\n"

        manifest = {"target": self.target_name, "type": output_type, "files": list(files.keys())}
        return manifest, files, warnings
