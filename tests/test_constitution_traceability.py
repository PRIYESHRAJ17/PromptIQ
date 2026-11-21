"""Tests for Project Constitution requirement traceability and contradiction detection."""

from promptiq.models.constitution import ProjectConstitution
from promptiq.services.constitution_service import ConstitutionService


def test_requirement_traceability_matrix():
    """Verifies that traceability matrix captures dependencies, verification methods, and status."""
    const = ProjectConstitution(
        project_id="proj-123",
        version=1,
        goals=["Build high-throughput event router"],
        requirements=[
            {
                "id": "REQ-001",
                "text": "System must process 10,000 events/sec",
                "category": "performance",
                "priority": "P0",
                "status": "confirmed",
                "provenance": "user_provided",
                "depends_on": [],
                "deliverable_target": "router.py",
                "verification_method": "deterministic_test",
                "verification_status": "verified",
                "outstanding_gaps": [],
            },
            {
                "id": "REQ-002",
                "text": "Dead letter queue persistence on delivery failure",
                "category": "reliability",
                "priority": "P1",
                "status": "confirmed",
                "provenance": "user_provided",
                "depends_on": ["REQ-001"],
                "deliverable_target": "dlq.py",
                "verification_method": "deterministic_test",
                "verification_status": "unverified",
                "outstanding_gaps": ["Integration test with broker disconnection"],
            },
        ],
        scope={"in_scope": ["event routing"], "out_of_scope": ["React frontend", "web UI"]},
        technical_direction={"prohibited_stack": ["Node.js", "MongoDB"]},
        decisions=[],
        assumptions=[],
        open_questions=[],
        risks=[],
        conflicts=[],
    )

    matrix = ConstitutionService.get_requirement_traceability_matrix(const)
    assert len(matrix) == 2
    assert matrix[0]["id"] == "REQ-001"
    assert matrix[0]["verification_status"] == "verified"
    assert matrix[1]["id"] == "REQ-002"
    assert matrix[1]["depends_on"] == ["REQ-001"]
    assert "Integration test" in matrix[1]["outstanding_gaps"][0]


def test_detect_prompt_contradictions():
    """Verifies contradiction detection against exclusions, prohibited stacks, and core invariants."""
    const = ProjectConstitution(
        project_id="proj-123",
        version=1,
        goals=["Backend event service"],
        requirements=[],
        scope={"out_of_scope": ["React frontend", "billing gateway"]},
        technical_direction={"prohibited_stack": ["MongoDB", "Express.js"]},
        decisions=[],
        assumptions=[],
        open_questions=[],
        risks=[],
        conflicts=[],
    )

    # 1. Scope violation
    c1 = ConstitutionService.detect_prompt_contradictions(
        const, "Please implement the billing gateway endpoint."
    )
    assert any("billing gateway" in c for c in c1)

    # 2. Prohibited stack violation
    c2 = ConstitutionService.detect_prompt_contradictions(const, "Use MongoDB for data storage.")
    assert any("MongoDB" in c for c in c2)

    # 3. Invariant: Strictly No Website Frontend
    c3 = ConstitutionService.detect_prompt_contradictions(
        const, "Please build React frontend dashboard for monitoring."
    )
    assert any("frontend" in c.lower() for c in c3)

    # 4. Invariant: Zero BYOK
    c4 = ConstitutionService.detect_prompt_contradictions(
        const, "Enter your OpenAI key to continue."
    )
    assert any("user api key" in c.lower() or "zero-byok" in c.lower() for c in c4)

    # 5. Invariant: No Local Inference
    c5 = ConstitutionService.detect_prompt_contradictions(
        const, "Please install Ollama to run the model locally."
    )
    assert any("local inference" in c.lower() or "ollama" in c.lower() for c in c5)

    # 6. Clean prompt
    c_clean = ConstitutionService.detect_prompt_contradictions(
        const, "Write a Python async queue worker in SQLite."
    )
    assert len(c_clean) == 0
