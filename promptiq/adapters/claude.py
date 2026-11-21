"""Claude Code native instructions adapter."""

import json
from typing import Any

from promptiq.adapters.base import BaseTargetAdapter
from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class ClaudeCodeTargetAdapter(BaseTargetAdapter):
    """Compiles PPS into Claude Code native CLAUDE.md and .claude configuration files."""

    target_name: str = "claude-code"
    capabilities: dict[str, Any] = {
        "context_window": 200000,
        "supports_mcp": True,
        "supports_subagents": True,
        "supports_artifacts": False,
        "supports_rules_hierarchy": True,
        "supports_tool_calling": True,
        "max_output_tokens": 4096,
        "multimodal": True,
    }

    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        files: dict[str, str] = {}
        warnings: list[str] = []

        reqs_text = "\n".join([f"- [{r.get('id', 'REQ')}] {r.get('text')}" for r in pps.requirements])
        exclusions_text = "\n".join([f"- {e}" for e in pps.constraints.get("out_of_scope", [])]) or "None."

        claude_md = (
            f"# CLAUDE.md — Project Instructions for Claude Code\n\n"
            f"## Objective\n{pps.intent.primary_objective}\n\n"
            f"## Requirements\n{reqs_text}\n\n"
            f"## Prohibited Choices & Out of Scope\n{exclusions_text}\n\n"
            f"## Workflow Rules\n"
            f"- Verify code changes with automated test runs.\n"
            f"- Do not bypass error handling or type checking.\n"
            f"- Respect least-privilege tool execution.\n"
        )

        if output_type == "prompt_only":
            files["CLAUDE.md"] = claude_md
            manifest = {"target": self.target_name, "type": "prompt_only", "files": ["CLAUDE.md"]}
            return manifest, files, warnings

        elif output_type == "prompt_suite":
            files["CLAUDE.md"] = claude_md
            files["DEVELOPER_BRIEF.md"] = f"# Developer Task Brief\n\n{pps.intent.primary_objective}\n"
            manifest = {"target": self.target_name, "type": "prompt_suite", "files": list(files.keys())}
            return manifest, files, warnings

        else:  # complete_package
            files["CLAUDE.md"] = claude_md
            files[".claude/settings.json"] = json.dumps(
                {
                    "permissions": {
                        "allowBash": True,
                        "allowFileEdit": True,
                        "requireApprovalForDeploy": True,
                    }
                },
                indent=2,
            )
            files[".claude/rules/architecture.md"] = (
                f"# Architectural Principles\n\n"
                f"- Pattern: {pps.constraints.get('technical', {}).get('architecture_pattern', 'modular_monolith')}\n"
                f"- Adhere to test-driven implementation.\n"
            )
            files["README.md"] = f"# Claude Code Instruction Package\n\nGoal: {pps.intent.primary_objective}\n"
            manifest = {"target": self.target_name, "type": "complete_package", "files": list(files.keys())}
            return manifest, files, warnings
