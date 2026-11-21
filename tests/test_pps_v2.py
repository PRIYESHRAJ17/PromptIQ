"""Tests for PPS v2.0.0 completeness validation, structured sections, and deterministic hashing."""


from promptiq.compiler.pps import PPSBuilder
from promptiq.models.constitution import ProjectConstitution
from promptiq.schemas.pps import (
    IntentSchema,
    OutputContractSchema,
    PromptSpecSchema,
    TargetProfileSchema,
)


def test_pps_v2_completeness_and_hash():
    """Tests completeness validation and SHA-256 deterministic fingerprinting in PPS v2.0.0."""
    target = TargetProfileSchema(
        host="google-antigravity",
        provider="google",
        model_id="gemini-3.8-flash",
    )
    const = ProjectConstitution(
        project_id="proj-999",
        version=1,
        is_approved=True,
        goals=["Build high-speed cache layer"],
        requirements=[
            {
                "id": "REQ-001",
                "text": "Cache eviction using LRU with O(1) complexity",
                "category": "functional",
                "priority": "P0",
                "provenance": "user_provided",
                "acceptance_criteria": "LRU eviction verified via unit tests",
            }
        ],
        scope={"out_of_scope": ["Web dashboard"]},
        technical_direction={"preferred_stack": ["Python", "Redis"]},
        decisions=[],
        assumptions=[],
        open_questions=[],
    )

    pps = PPSBuilder.build_from_constitution(const, target)

    assert pps.spec_version == "2.0.0"
    assert pps.role_and_responsibilities is not None
    assert "LRU" in pps.acceptance_criteria.items[0]
    assert pps.security_and_privacy.tenant_isolation_required is True

    # Validate completeness
    gaps = pps.validate_completeness()
    assert len(gaps) == 0

    # Deterministic hash
    h1 = pps.to_deterministic_hash()
    h2 = pps.to_deterministic_hash()
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 length


def test_pps_v2_completeness_catches_missing_fields():
    """Tests that incomplete PPS triggers validation errors."""
    incomplete_pps = PromptSpecSchema(
        project_id="p-1",
        constitution_version=1,
        intent=IntentSchema(primary_objective=""),  # Empty
        target_profile=TargetProfileSchema(host="", provider="openai", model_id="gpt-4o"),  # Empty host
        requirements=[],  # Empty requirements
        output_contract=OutputContractSchema(format="markdown", sections_required=[]),  # Empty sections
    )

    gaps = incomplete_pps.validate_completeness()
    assert len(gaps) >= 3
    assert any("Primary objective" in g for g in gaps)
    assert any("Target profile host" in g for g in gaps)
    assert any("No requirements" in g for g in gaps)
