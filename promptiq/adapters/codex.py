"""OpenAI Codex / Developer Agent instructions adapter."""

import json
from typing import Any

from promptiq.adapters.base import BaseTargetAdapter
from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class CodexTargetAdapter(BaseTargetAdapter):
    """Compiles PPS into modern OpenAI Codex / Agent developer instructions and MCP configurations.

    Note: Legacy ChatGPT Plugins (.well-known/ai-plugin.json) were officially sunset by OpenAI
    in April 2024. This adapter emits modern CODEX.md, AGENTS.md, .codex/instructions.md,
    and .codex/mcp.json specifications.
    """

    target_name: str = "openai-codex"
    capabilities: dict[str, Any] = {
        "context_window": 128000,
        "supports_mcp": False,
        "supports_subagents": False,
        "supports_artifacts": False,
        "supports_rules_hierarchy": False,
        "supports_tool_calling": True,
        "max_output_tokens": 4096,
        "multimodal": False,
    }

    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        files: dict[str, str] = {}
        warnings: list[str] = []

        reqs_text = "\n".join([f"- [{r.get('id', 'REQ')}] ({r.get('priority', 'P1')}): {r.get('text')}" for r in pps.requirements])
        exclusions_text = "\n".join([f"- {e}" for e in pps.constraints.get("out_of_scope", [])]) or "None specified."
        phases_text = "\n".join([f"{p.get('phase')}. **{p.get('name')}**: {p.get('objective')}" for p in pps.workflow_phases])

        codex_md = (
            f"# CODEX.md — Project Instructions for OpenAI Codex\n\n"
            f"## Objective\n{pps.intent.primary_objective}\n\n"
            f"## Target Audience\n{pps.intent.target_audience}\n\n"
            f"## Requirements\n{reqs_text}\n\n"
            f"## Constraints & Exclusions\n{exclusions_text}\n\n"
            f"## Execution Phases\n{phases_text}\n\n"
            f"## Invariants\n"
            f"- Verify all code changes with automated unit and integration tests.\n"
            f"- Strictly observe tenant isolation and zero-trust security boundaries.\n"
            f"- Never leak credentials or private user information.\n"
        )

        agents_md = (
            f"# AGENTS.md — Cross-Agent Workspace Instructions\n\n"
            f"## Objective\n{pps.intent.primary_objective}\n\n"
            f"## Rules & Guidelines\n"
            f"- Adhere to project architecture: {pps.constraints.get('technical', {}).get('architecture_pattern', 'modular_monolith')}\n"
            f"- Do not create frontend or UI components unless explicitly authorized.\n"
            f"- Write robust, idiomatic, clean code with full test coverage.\n"
        )

        if output_type == "prompt_only":
            files["CODEX.md"] = codex_md
            manifest = {"target": self.target_name, "type": "prompt_only", "files": ["CODEX.md"]}
            return manifest, files, warnings

        elif output_type == "prompt_suite":
            files["CODEX.md"] = codex_md
            files["AGENTS.md"] = agents_md
            files["DEVELOPER_TASK.md"] = (
                f"# Developer Task Brief\n\n"
                f"**Primary Objective**: {pps.intent.primary_objective}\n\n"
                f"**Success Criteria**:\n"
                + "\n".join([f"- {sc}" for sc in pps.intent.success_criteria])
                + "\n"
            )
            manifest = {"target": self.target_name, "type": "prompt_suite", "files": list(files.keys())}
            return manifest, files, warnings

        else:  # complete_package
            files["CODEX.md"] = codex_md
            files["AGENTS.md"] = agents_md
            files[".codex/instructions.md"] = (
                f"# System Instructions for Codex Agent\n\n"
                f"Objective: {pps.intent.primary_objective}\n\n"
                f"Requirements Checklist:\n{reqs_text}\n"
            )
            files[".codex/mcp.json"] = json.dumps(
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
            files["README.md"] = (
                f"# OpenAI Codex Configuration Package\n\n"
                f"**Project**: `{pps.project_id}`\n"
                f"**Goal**: {pps.intent.primary_objective}\n\n"
                f"Includes `CODEX.md`, `AGENTS.md`, `.codex/instructions.md`, and MCP configuration.\n"
            )
            manifest = {"target": self.target_name, "type": "complete_package", "files": list(files.keys())}
            return manifest, files, warnings
