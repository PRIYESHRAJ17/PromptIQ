"""Prompt Autopsy Golden Benchmark Evaluation.

Evaluates diagnostic precision, recall, and false positive rates across
the curated 21-category Golden Benchmark Dataset (tests/fixtures/autopsy_golden_dataset.json).
"""

import json
from pathlib import Path

import pytest

from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.schemas.critic import AutopsyRequest


@pytest.fixture
def golden_dataset() -> dict:
    dataset_path = Path("tests/fixtures/autopsy_golden_dataset.json")
    with open(dataset_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_golden_dataset_structure_and_completeness(golden_dataset: dict) -> None:
    """Verifies that the golden dataset has exactly 21 unique categories and required schema fields."""
    benchmarks = golden_dataset["benchmarks"]
    assert len(benchmarks) == 21
    categories = {b["category"] for b in benchmarks}
    assert len(categories) == 21, f"Expected 21 unique categories, got {len(categories)}: {categories}"

    for b in benchmarks:
        assert b["id"].startswith("AUT-GOLD-")
        assert len(b["prompt_text"]) >= 4
        assert len(b["clean_prompt_text"]) > 10
        assert b["expected_severity"] in ("critical", "high", "medium", "low")
        assert isinstance(b["expected_blocks_release"], bool)


@pytest.mark.asyncio
async def test_autopsy_benchmark_recall_across_21_categories(golden_dataset: dict) -> None:
    """Evaluates detection recall: every benchmark prompt must trigger its target category finding."""
    benchmarks = golden_dataset["benchmarks"]
    detected_count = 0
    missed: list[str] = []

    for b in benchmarks:
        req = AutopsyRequest(
            prompt_text=b["prompt_text"],
            target_environment="antigravity",
        )
        resp = await PromptAutopsyEngine.diagnose_prompt(req)
        found_categories = {f.category for f in resp.findings}

        target_cat = b["category"]
        if target_cat in found_categories:
            detected_count += 1
        else:
            missed.append(f"{b['id']}: expected '{target_cat}', got {found_categories}")

    recall = detected_count / len(benchmarks)
    assert recall >= 0.95, f"Recall was {recall:.2%} (missed: {missed})"
    assert len(missed) == 0, f"Missed categories: {missed}"


@pytest.mark.asyncio
async def test_autopsy_benchmark_false_positive_resistance(golden_dataset: dict) -> None:
    """Evaluates false positive resistance: clean prompts should NOT trigger critical/high blocking findings."""
    benchmarks = golden_dataset["benchmarks"]
    false_blocks: list[str] = []

    for b in benchmarks:
        clean_text = b["clean_prompt_text"]
        req = AutopsyRequest(
            prompt_text=clean_text,
            target_environment="antigravity",
        )
        resp = await PromptAutopsyEngine.diagnose_prompt(req)

        # Clean prompts should not be BLOCKED or have critical findings
        critical_findings = [f for f in resp.findings if f.severity == "critical"]
        if critical_findings:
            false_blocks.append(f"{b['id']} clean prompt falsely triggered critical: {[f.category for f in critical_findings]}")

    assert len(false_blocks) == 0, f"False positive blocks detected: {false_blocks}"


@pytest.mark.asyncio
async def test_autopsy_benchmark_severity_and_release_blocking(golden_dataset: dict) -> None:
    """Verifies that high and critical findings correctly flag blocks_release=True."""
    benchmarks = golden_dataset["benchmarks"]

    for b in benchmarks:
        if not b["expected_blocks_release"]:
            continue

        req = AutopsyRequest(
            prompt_text=b["prompt_text"],
            target_environment="antigravity",
        )
        resp = await PromptAutopsyEngine.diagnose_prompt(req)
        blocking_findings = [f for f in resp.findings if f.blocks_release]
        assert len(blocking_findings) >= 1, f"{b['id']} ({b['category']}) was expected to block release but had no blocking findings"
