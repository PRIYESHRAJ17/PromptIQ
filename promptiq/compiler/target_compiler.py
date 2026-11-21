"""Target Compiler coordinating PPS generation, adapter compilation, and validation."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.adapters import (
    AntigravityTargetAdapter,
    BaseTargetAdapter,
    ClaudeCodeTargetAdapter,
    CodexTargetAdapter,
    CursorTargetAdapter,
    GeminiCLITargetAdapter,
    RawPromptTargetAdapter,
)
from promptiq.compiler.pps import PPSBuilder
from promptiq.models.audit import AuditEvent
from promptiq.models.package import PromptPackage
from promptiq.models.spec import PromptSpecification
from promptiq.schemas.package import OutputType, PromptPackageResponse
from promptiq.schemas.pps import TargetProfileSchema
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.project_service import ProjectService


class TargetCompiler:
    """Compiles an approved Project Constitution into target-native packages."""

    def __init__(self):
        self._adapters: dict[str, BaseTargetAdapter] = {
            "google-antigravity": AntigravityTargetAdapter(),
            "claude-code": ClaudeCodeTargetAdapter(),
            "cursor": CursorTargetAdapter(),
            "openai-codex": CodexTargetAdapter(),
            "gemini-cli": GeminiCLITargetAdapter(),
            "raw-prompt": RawPromptTargetAdapter(),
            "portable-suite": RawPromptTargetAdapter(),
        }

    def get_adapter(self, target: str) -> BaseTargetAdapter:
        target_clean = target.lower().strip()
        if target_clean not in self._adapters:
            # Fall back to raw prompt if unknown, with warning
            return self._adapters["raw-prompt"]
        return self._adapters[target_clean]

    async def compile_package(
        self,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        target_environment: str = "google-antigravity",
        output_type: OutputType = "complete_package",
        surface: str = "api",
    ) -> PromptPackageResponse:
        """Executes full compilation from Constitution to validated PromptPackage."""
        project = await ProjectService.get_project(db, project_id, user_id)
        constitution = await ConstitutionService.get_current_constitution(db, project_id, user_id)

        target_profile = TargetProfileSchema(
            host=target_environment,
            provider="google" if "antigravity" in target_environment or "gemini" in target_environment else "anthropic",
            model_id="gemini-3.8-flash",
            tools_available=["read_file", "write_file", "run_command", "mcp"],
            permissions=["read", "write", "execute"],
        )

        # 1. Build canonical PPS
        pps = PPSBuilder.build_from_constitution(constitution, target_profile)

        # Persist PPS in database
        spec_record = PromptSpecification(
            project_id=project.id,
            constitution_version=constitution.version,
            intent=pps.intent.model_dump(),
            target_profile=pps.target_profile.model_dump(),
            requirements=pps.requirements,
            constraints=pps.constraints,
            tools_and_permissions=pps.tools_and_permissions,
            workflow=pps.workflow_phases,
            deliverables=[d.model_dump() for d in pps.deliverables],
            output_contract=pps.output_contract.model_dump(),
            validation_plan=pps.validation_plan,
            provenance=pps.provenance_trail,
        )
        db.add(spec_record)
        await db.flush()

        # 2. Resolve adapter and compile
        adapter = self.get_adapter(target_environment)
        manifest, files, warnings = adapter.compile(pps, output_type)

        # 3. Validation Gate
        is_validated = True
        validation_errors = []

        # Ensure no empty files
        for path, content in files.items():
            if not content.strip():
                is_validated = False
                validation_errors.append(f"File '{path}' is empty")

        # Ensure requirements are present in the package files
        combined_text = " ".join(files.values())
        for req in pps.requirements:
            req_id = req.get("id")
            if req_id and req_id not in combined_text:
                warnings.append(f"Requirement '{req_id}' not explicitly cited in compiled text.")

        validation_result = {
            "status": "passed" if is_validated else "failed",
            "errors": validation_errors,
            "checked_requirements_count": len(pps.requirements),
        }

        # 4. Persist compiled package
        package = PromptPackage(
            project_id=project.id,
            spec_id=spec_record.id,
            target_environment=target_environment,
            output_type=output_type,
            manifest=manifest,
            files=files,
            warnings=warnings,
            is_validated=is_validated,
            validation_result=validation_result,
        )
        db.add(package)

        # Log audit trail
        audit = AuditEvent(
            workspace_id=project.workspace_id,
            project_id=project.id,
            user_id=user_id,
            action="package.compiled",
            surface=surface,
            payload={
                "target": target_environment,
                "output_type": output_type,
                "files_count": len(files),
            },
        )
        db.add(audit)
        await db.flush()

        return PromptPackageResponse.model_validate(package)

    def recommend_target(self, constitution_or_reqs: Any = None) -> dict[str, Any]:
        """Analyzes project requirements and characteristics to recommend the optimal execution target."""
        feature_support = {
            "google-antigravity": {
                "mcp": True,
                "subagents": True,
                "multi_turn_artifacts": True,
                "browser_sandbox": True,
                "hierarchical_rules": True,
            },
            "claude-code": {
                "mcp": True,
                "subagents": True,
                "multi_turn_artifacts": False,
                "browser_sandbox": False,
                "hierarchical_rules": True,
            },
            "cursor": {
                "mcp": False,
                "subagents": False,
                "multi_turn_artifacts": False,
                "browser_sandbox": False,
                "hierarchical_rules": True,
            },
            "openai-codex": {
                "mcp": False,
                "subagents": False,
                "multi_turn_artifacts": False,
                "browser_sandbox": False,
                "hierarchical_rules": False,
            },
            "gemini-cli": {
                "mcp": False,
                "subagents": False,
                "multi_turn_artifacts": False,
                "browser_sandbox": False,
                "hierarchical_rules": False,
            },
            "raw-prompt": {
                "mcp": False,
                "subagents": False,
                "multi_turn_artifacts": False,
                "browser_sandbox": False,
                "hierarchical_rules": False,
            },
        }

        needs_mcp = False
        needs_subagents = False
        needs_browser = False

        if constitution_or_reqs:
            req_text = ""
            if hasattr(constitution_or_reqs, "requirements"):
                req_text = " ".join(
                    str(r.get("text", "") if isinstance(r, dict) else getattr(r, "text", ""))
                    for r in constitution_or_reqs.requirements
                ).lower()
            elif isinstance(constitution_or_reqs, dict):
                req_text = str(constitution_or_reqs).lower()
            elif isinstance(constitution_or_reqs, str):
                req_text = constitution_or_reqs.lower()

            if "mcp" in req_text or "tool" in req_text or "integration" in req_text:
                needs_mcp = True
            if "agent" in req_text or "multi-agent" in req_text or "orchestrat" in req_text:
                needs_subagents = True
            if "browser" in req_text or "web search" in req_text:
                needs_browser = True

        scores = {
            "google-antigravity": round(0.85 + (0.05 if needs_mcp else 0.0) + (0.05 if needs_subagents else 0.0) + (0.05 if needs_browser else 0.0), 2),
            "claude-code": round(0.80 + (0.05 if needs_mcp else 0.0) + (0.05 if needs_subagents else 0.0), 2),
            "cursor": 0.75,
            "openai-codex": 0.65,
            "gemini-cli": 0.60,
            "raw-prompt": 0.50,
        }

        best_target = max(scores, key=scores.get)

        pros_map = {
            "google-antigravity": [
                "Full multi-agent architecture and autonomous tool orchestration",
                "Built-in artifact rendering and interactive review flows",
                "Direct native MCP tool protocol support",
                "Comprehensive hierarchical rules and GEMINI.md support",
            ],
            "claude-code": [
                "Terminal-native agentic development and git automation",
                "Native subagent delegation and bash execution",
                "CLAUDE.md integration instructions",
            ],
            "cursor": [
                "Seamless in-editor integration with .cursorrules",
                "Inline code generation and multi-file composer awareness",
            ],
            "openai-codex": [
                "Clean declarative system instructions for API-driven agents",
            ],
            "gemini-cli": [
                "Zero-configuration CLI agent script execution",
            ],
            "raw-prompt": [
                "Universal portability to any LLM interface",
            ],
        }

        cons_map = {
            "google-antigravity": [
                "Requires Google Antigravity or compatible agent runner",
            ],
            "claude-code": [
                "No native generative UI or visual artifact rendering",
            ],
            "cursor": [
                "Lacks MCP server and autonomous background tool execution",
            ],
            "openai-codex": [
                "Does not support hierarchical workspace rules or subagents",
            ],
            "gemini-cli": [
                "Limited tool ecosystem compared to Antigravity and Claude",
            ],
            "raw-prompt": [
                "No tool execution, filesystem access, or agent lifecycle management",
            ],
        }

        rationale = (
            f"Target '{best_target}' provides optimal compatibility based on project requirements. "
            f"It supports {'MCP tools, ' if needs_mcp else ''}{'multi-agent delegation, ' if needs_subagents else ''}"
            f"and provides native instruction packaging."
        )

        return {
            "recommended_target": best_target,
            "rationale": rationale,
            "pros": pros_map.get(best_target, []),
            "cons": cons_map.get(best_target, []),
            "compatibility_scores": scores,
            "feature_support": feature_support,
        }

    async def compile_multi_target(
        self,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        targets: list[str],
        output_type: OutputType = "complete_package",
        surface: str = "api",
    ) -> dict[str, Any]:
        """Compiles package across multiple target environments in a single operation."""
        packages: dict[str, Any] = {}
        failures: dict[str, str] = {}

        for target in targets:
            try:
                pkg_resp = await self.compile_package(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    target_environment=target,
                    output_type=output_type,
                    surface=surface,
                )
                packages[target] = pkg_resp
            except Exception as e:
                failures[target] = str(e)

        return {
            "project_id": project_id,
            "packages": packages,
            "failures": failures,
        }


target_compiler = TargetCompiler()
