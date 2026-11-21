"""Cursor rules and configuration adapter."""

import json
from typing import Any

from promptiq.adapters.base import BaseTargetAdapter
from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class CursorTargetAdapter(BaseTargetAdapter):
    """Compiles PPS into .cursorrules and .cursor/rules/*.mdc files."""

    target_name: str = "cursor"
    capabilities: dict[str, Any] = {
        "context_window": 128000,
        "supports_mcp": False,
        "supports_subagents": False,
        "supports_artifacts": False,
        "supports_rules_hierarchy": True,
        "supports_tool_calling": True,
        "max_output_tokens": 4096,
        "multimodal": False,
    }

    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        files: dict[str, str] = {}
        warnings: list[str] = []

        reqs_text = "\n".join([f"- {r.get('id')}: {r.get('text')}" for r in pps.requirements])
        cursorrules = (
            f"# Cursor Rules for {pps.intent.primary_objective}\n\n"
            f"## Core Directives\n"
            f"- Fulfill requirements:\n{reqs_text}\n\n"
            f"## Constraints\n"
            f"- No arbitrary unapproved edits.\n"
            f"- Verify all code with tests.\n"
        )

        files[".cursorrules"] = cursorrules

        if output_type == "complete_package":
            files[".cursor/rules/requirements.mdc"] = (
                f"---\n"
                f"description: Confirmed project requirements\n"
                f"globs: **/*\n"
                f"---\n\n"
                f"# Requirements\n{reqs_text}\n"
            )
            files[".cursor/mcp.json"] = json.dumps(
                {
                    "mcpServers": {
                        "promptiq": {
                            "command": "python",
                            "args": ["-m", "promptiq.mcp.server"],
                        }
                    }
                },
                indent=2,
            )
            files["README.md"] = f"# Cursor Configuration Bundle\n\nObjective: {pps.intent.primary_objective}\n"

        manifest = {"target": self.target_name, "type": output_type, "files": list(files.keys())}
        return manifest, files, warnings
