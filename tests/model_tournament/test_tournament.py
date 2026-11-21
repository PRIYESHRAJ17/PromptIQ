"""Test Model Intelligence Tournament Execution and Category Coverage."""

import pytest

from promptiq.eval.tournament import ModelTournamentRunner


def test_tournament_dataset_completeness():
    """Verifies that the synthetic benchmark dataset covers all 14 mandatory tournament categories."""
    runner = ModelTournamentRunner()
    cases = runner.load_test_cases()

    assert len(cases) == 14, "Must contain exactly 14 category test cases"

    expected_categories = {
        "complex_reasoning",
        "software_discovery",
        "requirement_extraction",
        "prompt_engineering",
        "prompt_improvement",
        "critical_review",
        "research_synthesis",
        "coding_debugging",
        "long_context_understanding",
        "structured_output",
        "tool_use",
        "multi_stage_consistency",
        "instruction_following",
        "robustness",
    }

    found_categories = {c["category"] for c in cases}
    assert found_categories == expected_categories, f"Missing categories: {expected_categories - found_categories}"


@pytest.mark.asyncio
async def test_tournament_execution_harness():
    """Executes the tournament runner against the deterministic mock harness."""
    runner = ModelTournamentRunner()
    report = await runner.evaluate_candidate(
        candidate_name="PromptIQ Reference Harness",
        adapter_route="mock",
    )

    assert "overall_score" in report
    assert "pass_rate_pct" in report
    assert report["total_cases"] == 14
    assert len(report["category_scores"]) == 14
    assert report["avg_latency_ms"] >= 0.0
