"""Target Compiler coordinating PPS generation, adapter compilation, and validation."""

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
        cls,
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
            model_id="gemini-2.0-flash",
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
        compiler_instance = TargetCompiler()
        adapter = compiler_instance.get_adapter(target_environment)
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


target_compiler = TargetCompiler()
