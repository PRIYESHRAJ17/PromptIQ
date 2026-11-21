"""PromptIQ Prompt Specification (PPS v2.0.0) intermediate representation generator."""

from promptiq.core.exceptions import ConstitutionApprovalRequiredError
from promptiq.models.constitution import ProjectConstitution
from promptiq.schemas.pps import (
    AcceptanceCriteriaSchema,
    BehaviorRulesSchema,
    DeliverableItem,
    ExpectedOutputSchema,
    FailureHandlingSchema,
    InputVariableSchema,
    IntentSchema,
    OutputContractSchema,
    PromptSpecSchema,
    ResearchReferenceSchema,
    RoleAndResponsibilities,
    SecurityPrivacySchema,
    TargetProfileSchema,
)


class PPSBuilder:
    """Transforms an approved Project Constitution into a typed, vendor-neutral PPS v2.0.0 intermediate representation."""

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
            success_criteria=[
                r.get("acceptance_criteria")
                if isinstance(r, dict)
                else getattr(r, "acceptance_criteria", None)
                for r in constitution.requirements
                if (
                    r.get("acceptance_criteria")
                    if isinstance(r, dict)
                    else getattr(r, "acceptance_criteria", None)
                )
            ],
        )

        # Map requirements with IDs and traceability
        requirements_payload = []
        for req in constitution.requirements:
            if isinstance(req, dict):
                r_id = req.get("id")
                r_text = req.get("text")
                r_cat = req.get("category", "functional")
                r_prio = req.get("priority", "P1")
                r_prov = req.get("provenance", "user_provided")
                r_crit = req.get("acceptance_criteria")
                r_dep = req.get("depends_on", [])
                r_meth = req.get("verification_method", "deterministic_test")
            else:
                r_id = getattr(req, "id", None)
                r_text = getattr(req, "text", None)
                r_cat = getattr(req, "category", "functional")
                r_prio = getattr(req, "priority", "P1")
                r_prov = getattr(req, "provenance", "user_provided")
                r_crit = getattr(req, "acceptance_criteria", None)
                r_dep = getattr(req, "depends_on", [])
                r_meth = getattr(req, "verification_method", "deterministic_test")

            requirements_payload.append(
                {
                    "id": r_id,
                    "text": r_text,
                    "category": r_cat,
                    "priority": r_prio,
                    "provenance": r_prov,
                    "acceptance_criteria": r_crit,
                    "depends_on": r_dep,
                    "verification_method": r_meth,
                }
            )

        constraints = {
            "prohibited_actions": [
                "No arbitrary unapproved file mutations",
                "No bypass of tenant isolation",
                "No embedding of credentials or secrets",
                "No generation of website frontend UI unless authorized",
            ],
            "technical": constitution.technical_direction or {},
            "out_of_scope": (constitution.scope or {}).get("out_of_scope", []),
        }

        tools_and_perms = {
            "default_mode": "read_only",
            "write_requires_approval": True,
            "allowed_tools": target_profile.tools_available
            or ["read_file", "write_file", "run_command"],
            "permissions": target_profile.permissions or ["read", "write", "execute"],
        }

        workflow_phases = [
            {
                "phase": 1,
                "name": "Context & Requirements Alignment",
                "objective": "Verify understanding of all requirements",
            },
            {
                "phase": 2,
                "name": "Architecture & Scaffolding",
                "objective": "Establish clean modular boundaries",
            },
            {
                "phase": 3,
                "name": "Implementation & Testing",
                "objective": "Deliver verified, tested code",
            },
            {
                "phase": 4,
                "name": "Verification & Review",
                "objective": "Run automated checks and independent review",
            },
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
                "Deterministic verification passes before sign-off",
            ],
            manifest_required=True,
        )

        role_and_responsibilities = RoleAndResponsibilities(
            role_title=f"Expert Engineer: {primary_obj[:60]}",
            responsibilities=[
                "Execute implementation strictly meeting confirmed requirements",
                "Enforce tenant isolation and zero-price execution invariants",
                "Provide deterministic verification evidence",
            ],
            non_responsibilities=[
                "Do not introduce frontend pages or UI mockups",
                "Do not store or prompt for user API keys",
                "Do not assume unverified requirements",
            ],
        )

        behavior_rules = BehaviorRulesSchema(
            preservation_rules=[
                "Preserve all existing passing test suites",
                "Preserve database schema migrations and tenant isolation checks",
            ],
            prohibitions=[
                "Never request or log API credentials or tokens",
                "Never initiate paid cloud routes",
                "Never bypass access controls or permission checks",
            ],
            operational_guidelines=[
                "Verify actual state before declaring completion",
                "Document evidence with exact request IDs and test output",
            ],
        )

        security_and_privacy = SecurityPrivacySchema(
            tenant_isolation_required=True,
            zero_key_storage=True,
            secret_leakage_prevention=True,
            sanitization_rules=[
                "Sanitize untrusted external inputs against prompt injection",
                "Pin outbound sockets against SSRF and DNS rebinding",
            ],
        )

        failure_handling = FailureHandlingSchema(
            fallback_action="halt_and_report",
            escalation_conditions=[
                "Upstream capacity exhausted (HTTP 429)",
                "Contradiction detected between requirements and proposed action",
                "Required file or resource not found",
            ],
            retry_policy={
                "max_retries": 2,
                "backoff_strategy": "exponential",
                "initial_delay_seconds": 1.0,
            },
        )

        acceptance_criteria = AcceptanceCriteriaSchema(
            items=[
                r["acceptance_criteria"]
                for r in requirements_payload
                if r.get("acceptance_criteria")
            ],
            test_harness="pytest --cov=promptiq",
        )

        return PromptSpecSchema(
            spec_version="2.0.0",
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
            role_and_responsibilities=role_and_responsibilities,
            input_variables=[
                InputVariableSchema(
                    name="user_query", description="Primary user instruction", required=True
                ),
                InputVariableSchema(
                    name="execution_context", description="Operational parameters", required=False
                ),
            ],
            expected_output=ExpectedOutputSchema(
                primary_deliverable="Complete instruction package or code artifacts",
                format="target_native",
                sections=["Overview", "Architecture", "Implementation", "Verification"],
            ),
            behavior_rules=behavior_rules,
            security_and_privacy=security_and_privacy,
            failure_handling=failure_handling,
            research_references=ResearchReferenceSchema(
                citations=[],
                evidence_ledger_ref=None,
            ),
            acceptance_criteria=acceptance_criteria,
        )
