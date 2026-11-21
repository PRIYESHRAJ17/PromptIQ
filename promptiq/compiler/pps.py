"""PromptIQ Prompt Specification (PPS) intermediate representation generator."""

from promptiq.core.exceptions import ConstitutionApprovalRequiredError
from promptiq.models.constitution import ProjectConstitution
from promptiq.schemas.pps import (
    DeliverableItem,
    IntentSchema,
    OutputContractSchema,
    PromptSpecSchema,
    TargetProfileSchema,
)


class PPSBuilder:
    """Transforms an approved Project Constitution into a typed, vendor-neutral PPS intermediate representation."""

    @classmethod
    def build_from_constitution(
        cls,
        constitution: ProjectConstitution,
        target_profile: TargetProfileSchema,
        require_approval: bool = True,
    ) -> PromptSpecSchema:
        """Validates approval and builds the canonical PPS model."""
        if require_approval and not constitution.is_approved:
            raise ConstitutionApprovalRequiredError(
                f"Constitution v{constitution.version} is not approved. Please review and approve before compiling."
            )

        # Primary objective
        primary_obj = constitution.goals[0] if constitution.goals else "Deliver software solution"

        intent = IntentSchema(
            task_type="software_project",
            primary_objective=primary_obj,
            target_audience="developers",
            success_criteria=[r["acceptance_criteria"] for r in constitution.requirements if r.get("acceptance_criteria")],
        )

        # Map requirements with IDs
        requirements_payload = []
        for req in constitution.requirements:
            requirements_payload.append({
                "id": req.get("id"),
                "text": req.get("text"),
                "category": req.get("category", "functional"),
                "priority": req.get("priority", "P1"),
                "provenance": req.get("provenance", "user_provided"),
                "acceptance_criteria": req.get("acceptance_criteria"),
            })

        constraints = {
            "prohibited_actions": [
                "No arbitrary unapproved file mutations",
                "No bypass of tenant isolation",
                "No embedding of credentials or secrets",
            ],
            "technical": constitution.technical_direction,
            "out_of_scope": constitution.scope.get("out_of_scope", []),
        }

        tools_and_perms = {
            "default_mode": "read_only",
            "write_requires_approval": True,
            "allowed_tools": target_profile.tools_available or ["read_file", "write_file", "run_command"],
        }

        workflow_phases = [
            {"phase": 1, "name": "Context & Requirements Alignment", "objective": "Verify understanding of all requirements"},
            {"phase": 2, "name": "Architecture & Scaffolding", "objective": "Establish clean modular boundaries"},
            {"phase": 3, "name": "Implementation & Testing", "objective": "Deliver verified, tested code"},
            {"phase": 4, "name": "Verification & Review", "objective": "Run automated checks and independent review"},
        ]

        deliverables = [
            DeliverableItem(
                path="README.md",
                format="text/markdown",
                description="Project documentation, setup instructions, and architecture overview",
            )
        ]

        output_contract = OutputContractSchema(
            format="target_native",
            sections_required=["Context", "Requirements", "Constraints", "Execution Steps"],
            rules_and_invariants=[
                "Zero secret leakage",
                "Strict adherence to confirmed requirements",
            ],
            manifest_required=True,
        )

        return PromptSpecSchema(
            spec_version="1.0.0",
            project_id=constitution.project_id,
            constitution_version=constitution.version,
            intent=intent,
            target_profile=target_profile,
            requirements=requirements_payload,
            constraints=constraints,
            tools_and_permissions=tools_and_perms,
            workflow_phases=workflow_phases,
            deliverables=deliverables,
            output_contract=output_contract,
            validation_plan={"acceptance_tests_count": len(intent.success_criteria)},
            provenance_trail={"constitution_id": constitution.id, "version": constitution.version},
        )
