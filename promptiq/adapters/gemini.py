"""Gemini CLI Extension adapter."""

import json
from typing import Any

from promptiq.adapters.base import BaseTargetAdapter
from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class GeminiCLITargetAdapter(BaseTargetAdapter):
    """Compiles PPS into Gemini CLI extensions and context files."""

    target_name: str = "gemini-cli"

    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        files: dict[str, str] = {}
        warnings: list[str] = []

        reqs_text = "\n".join([f"- {r.get('id')}: {r.get('text')}" for r in pps.requirements])

        extension_json = {
            "name": f"promptiq-ext-{pps.project_id[:6]}",
            "version": "1.0.0",
            "description": pps.intent.primary_objective,
            "context_files": ["context/instructions.md"],
        }

        files["gemini-extension.json"] = json.dumps(extension_json, indent=2)
        files["context/instructions.md"] = (
            f"# GEMINI CLI INSTRUCTIONS\n\n"
            f"## Objective\n{pps.intent.primary_objective}\n\n"
            f"## Requirements\n{reqs_text}\n"
        )

        if output_type == "complete_package":
            files["commands/run.sh"] = "#!/bin/bash\necho 'Executing PromptIQ task...'\n"
            files["README.md"] = f"# Gemini CLI Extension Package\n\nObjective: {pps.intent.primary_objective}\n"

        manifest = {"target": self.target_name, "type": output_type, "files": list(files.keys())}
        return manifest, files, warnings
