"""Google Antigravity native plugin adapter."""

import json
from typing import Any

from promptiq.adapters.base import BaseTargetAdapter
from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class AntigravityTargetAdapter(BaseTargetAdapter):
    """Compiles PPS into Google Antigravity native plugin bundles."""

    target_name: str = "google-antigravity"

    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        files: dict[str, str] = {}
        warnings: list[str] = []

        reqs_text = "\n".join([f"- [{r.get('id', 'REQ')}] ({r.get('priority', 'P1')} - {r.get('provenance', 'user_provided')}): {r.get('text')}" for r in pps.requirements])
        exclusions_text = "\n".join([f"- {e}" for e in pps.constraints.get("out_of_scope", [])]) or "None specified."
        phases_text = "\n".join([f"{p.get('phase')}. **{p.get('name')}**: {p.get('objective')}" for p in pps.workflow_phases])

        if output_type == "prompt_only":
            prompt = (
                f"# MISSION: {pps.intent.primary_objective}\n\n"
                f"## TARGET AUDIENCE: {pps.intent.target_audience}\n\n"
                f"## REQUIREMENTS:\n{reqs_text}\n\n"
                f"## EXCLUSIONS & CONSTRAINTS:\n{exclusions_text}\n\n"
                f"## WORKFLOW:\n{phases_text}\n\n"
                f"## INVARIANTS:\n- Maintain strict verification and automated tests.\n- Never leak secrets or private data.\n"
            )
            files["prompt.md"] = prompt
            manifest = {"target": self.target_name, "type": "prompt_only", "files": ["prompt.md"]}
            return manifest, files, warnings

        elif output_type == "prompt_suite":
            system_prompt = (
                f"You are Antigravity, an elite software engineering agent.\n"
                f"Objective: {pps.intent.primary_objective}\n\n"
                f"Confirmed Requirements:\n{reqs_text}\n\n"
                f"Constraints:\n{exclusions_text}\n"
            )
            user_prompt = (
                "Begin execution of Phase 1: Context & Requirements Alignment.\n"
                "Success Criteria:\n" + "\n".join([f"- {sc}" for sc in pps.intent.success_criteria])
            )
            files["system_instructions.md"] = system_prompt
            files["user_task.md"] = user_prompt
            manifest = {"target": self.target_name, "type": "prompt_suite", "files": list(files.keys())}
            return manifest, files, warnings

        else:  # complete_package
            manifest = {
                "name": f"promptiq-{pps.project_id[:8]}",
                "version": "1.0.0",
                "description": pps.intent.primary_objective,
                "target": self.target_name,
                "skills": ["implementation"],
                "rules": ["invariants"],
                "permissions": pps.tools_and_permissions.get("allowed_tools", []),
            }
            files["plugin.json"] = json.dumps(manifest, indent=2)

            # AGENTS.md workspace instructions
            files["AGENTS.md"] = (
                f"# AGENTS WORKSPACE INSTRUCTIONS\n\n"
                f"## PRIMARY OBJECTIVE\n{pps.intent.primary_objective}\n\n"
                f"## CONFIRMED REQUIREMENTS\n{reqs_text}\n\n"
                f"## SCOPE EXCLUSIONS\n{exclusions_text}\n\n"
                f"## WORKFLOW PHASES\n{phases_text}\n"
            )

            # Skill definition
            files["skills/implementation/SKILL.md"] = (
                f"---\n"
                f"name: implementation-guide\n"
                f"description: Step-by-step execution guide for {pps.intent.primary_objective}\n"
                f"---\n\n"
                f"# Implementation Skill\n\n"
                f"## Instructions\n"
                f"1. Implement all confirmed requirements according to defined priorities.\n"
                f"2. Validate deliverables against acceptance criteria.\n"
            )

            # Workspace rules
            files["rules/project_invariants.md"] = (
                "# Project Invariants & Safety Rules\n\n"
                "- Read-only by default; explicit approval required for file mutations.\n"
                "- Enforce 100% automated test coverage for critical paths.\n"
                "- Zero credential exposure.\n"
            )

            files["README.md"] = (
                f"# PromptIQ Native Antigravity Package\n\n"
                f"**Project**: `{pps.project_id}`\n"
                f"**Goal**: {pps.intent.primary_objective}\n\n"
                f"Load this package into Google Antigravity as a native plugin.\n"
            )

            return manifest, files, warnings
