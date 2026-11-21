"""Test Model Intelligence Tournament Execution and Category Coverage."""

import pytest

from promptiq.eval.tournament import ModelTournamentRunner


def test_tournament_dataset_completeness():
    """Verifies that the versioned benchmark dataset covers all 20 mandatory tournament categories."""
    runner = ModelTournamentRunner()
    cases = runner.load_test_cases()

    assert len(cases) == 20, "Must contain exactly 20 category test cases"

    expected_categories = {
        "requirement_extraction",
        "adaptive_discovery",
        "project_planning",
        "constitution_generation",
        "technical_architecture",
        "complex_reasoning",
        "contradiction_detection",
        "prompt_engineering",
        "prompt_improvement",
        "critical_prompt_autopsy",
        "research_synthesis",
        "coding_and_debugging",
        "structured_json",
        "tool_calling",
        "long_context_handling",
        "instruction_adherence",
        "security_and_injection",
        "multi_stage_consistency",
        "robustness_under_ambiguity",
        "output_verification",
    }

    found_categories = {c["category"] for c in cases}
    assert found_categories == expected_categories, (
        f"Missing categories: {expected_categories - found_categories}"
    )


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
    assert report["total_cases"] == 20
    assert len(report["category_scores"]) == 20
    assert report["avg_latency_ms"] >= 0.0


@pytest.mark.asyncio
async def test_model_combination_quality_evaluation():
    """Evaluates empirical trade-offs across 4 multi-model architectural configurations."""
    runner = ModelTournamentRunner()
    report = await runner.evaluate_model_combinations(adapter_route="mock", sample_limit=5)

    assert "configurations_evaluated" in report
    configs = report["configurations_evaluated"]
    assert "config_a_single_model" in configs
    assert "config_b_generator_critic" in configs
    assert "config_c_gen_critic_deterministic" in configs
    assert "config_d_specialist_orchestration" in configs

    # Verify Config D and C have higher defect prevention than Config A
    assert (
        configs["config_d_specialist_orchestration"]["defect_prevention_rate_pct"]
        > configs["config_a_single_model"]["defect_prevention_rate_pct"]
    )
    assert (
        configs["config_c_gen_critic_deterministic"]["defect_prevention_rate_pct"]
        > configs["config_a_single_model"]["defect_prevention_rate_pct"]
    )
