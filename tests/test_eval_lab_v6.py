"""Evaluation of Test Lab V6 Benchmark Suite across all 10 Task Families."""

import json
from pathlib import Path


def load_test_lab_v6_benchmark():
    fixture_path = Path(__file__).parent / "fixtures" / "test_lab_benchmark_v6.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def test_lab_benchmark_structure_and_completeness():
    """Validates that the Test Lab benchmark contains exactly 100 cases across 10 families."""
    data = load_test_lab_v6_benchmark()
    assert data["total_cases"] == 100
    assert data["task_families_covered"] == 10
    cases = data["test_cases"]
    assert len(cases) == 100

    families = {}
    tiers = {}
    for c in cases:
        fam = c["task_family"]
        families[fam] = families.get(fam, 0) + 1
        tier = c["evaluation_tier"]
        tiers[tier] = tiers.get(tier, 0) + 1

    # Verify exactly 10 cases per family
    assert len(families) == 10
    for fam, count in families.items():
        assert count == 10, f"Task family {fam} has {count} cases instead of 10!"

    # Verify all 4 tiers are represented
    assert "deterministic_assertion" in tiers
    assert "schema_validation" in tiers
    assert "rule_based" in tiers
    assert "model_based" in tiers


def test_lab_evaluation_tier_separation():
    """Verifies that evaluation tiers remain strictly separated and traceable."""
    data = load_test_lab_v6_benchmark()
    cases = data["test_cases"]

    deterministic = [c for c in cases if c["evaluation_tier"] == "deterministic_assertion"]
    schema = [c for c in cases if c["evaluation_tier"] == "schema_validation"]
    rule_based = [c for c in cases if c["evaluation_tier"] == "rule_based"]
    model_based = [c for c in cases if c["evaluation_tier"] == "model_based"]

    assert len(deterministic) >= 40, "Deterministic assertion cases must be primary"
    assert len(schema) >= 15, "Schema validation cases must be present"
    assert len(rule_based) >= 20, "Rule-based cases must be present"
    assert len(model_based) >= 5, "Model-based evaluation cases must be present"


def test_lab_execution_against_synthetic_deliverable():
    """Executes assertions against a representative compliant deliverable and measures pass rates."""
    data = load_test_lab_v6_benchmark()
    cases = data["test_cases"]

    # Sample deliverable text incorporating software engineering and agent requirements
    sample_text = """
    # POST /api/v1/orders
    async with session.begin():
        query = select(Order).where(Order.workspace_id == ws_id)
    # Handled via ValidationError or WorkflowError
    raise ValidationError("Invalid order", code="VALIDATION_FAILED")
    idempotency_key = "abc-123"
    op.create_table("orders")
    422 Unprocessable Entity
    USER 10001
    correlation_id: req-001
    """

    se_cases = [c for c in cases if c["task_family"] == "software_engineering"]
    passed = 0
    for c in se_cases:
        pats = c["expected_patterns"]
        a_type = c["assertion_type"]
        if a_type == "contains":
            if all(p in sample_text for p in pats):
                passed += 1
        elif a_type == "not_contains":
            if not any(p in sample_text for p in pats):
                passed += 1

    # In sample_text, all 10 SE cases should pass
    assert passed == 10, f"Expected 10/10 SE cases to pass, got {passed}"
