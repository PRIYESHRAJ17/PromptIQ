"""Comprehensive Prompt Autopsy V7 Benchmark Evaluation Suite (300 cases across 3 splits)."""

import json
from pathlib import Path

import pytest

from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.schemas.critic import AutopsyRequest

BENCHMARK_PATH = Path("tests/fixtures/autopsy_benchmark_v7.json")


def load_benchmark_split(split_name: str) -> list[dict]:
    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [item for item in data["items"] if item["split"] == split_name]


@pytest.mark.asyncio
async def test_autopsy_v7_development_split_metrics():
    dev_items = load_benchmark_split("dev")
    assert len(dev_items) == 150

    true_positives = 0
    false_negatives = 0
    false_blocks = 0
    total_compliant = 0

    for item in dev_items:
        prompt_text = item["prompt_text"]
        expected_defects = item["expected_defects"]
        expected_blocked = item["expected_release_blocked"]

        req = AutopsyRequest(
            prompt_text=prompt_text,
            task_type=item["task_family"],
            target_environment="google-antigravity",
        )
        report = await PromptAutopsyEngine.diagnose_prompt(req)

        is_blocked = report.verdict in ("blocked", "needs_revision", "unsuitable")

        if not expected_defects:
            total_compliant += 1
            if is_blocked:
                false_blocks += 1
        else:
            if expected_blocked:
                if is_blocked:
                    true_positives += 1
                else:
                    false_negatives += 1

    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 1.0
    )
    fp_block_rate = false_blocks / total_compliant if total_compliant > 0 else 0.0

    assert recall >= 0.95, f"Dev recall below threshold: {recall:.2f}"
    assert fp_block_rate <= 0.05, f"Dev false-positive block rate exceeded: {fp_block_rate:.2f}"


@pytest.mark.asyncio
async def test_autopsy_v7_validation_split_metrics():
    val_items = load_benchmark_split("val")
    assert len(val_items) == 75

    true_positives = 0
    false_negatives = 0
    false_blocks = 0
    total_compliant = 0

    for item in val_items:
        req = AutopsyRequest(
            prompt_text=item["prompt_text"],
            task_type=item["task_family"],
            target_environment="google-antigravity",
        )
        report = await PromptAutopsyEngine.diagnose_prompt(req)
        is_blocked = report.verdict in ("blocked", "needs_revision", "unsuitable")

        if not item["expected_defects"]:
            total_compliant += 1
            if is_blocked:
                false_blocks += 1
        else:
            if item["expected_release_blocked"]:
                if is_blocked:
                    true_positives += 1
                else:
                    false_negatives += 1

    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 1.0
    )
    fp_block_rate = false_blocks / total_compliant if total_compliant > 0 else 0.0

    assert recall >= 0.95, f"Val recall below threshold: {recall:.2f}"
    assert fp_block_rate <= 0.05, f"Val false-positive block rate exceeded: {fp_block_rate:.2f}"


@pytest.mark.asyncio
async def test_autopsy_v7_held_out_evaluation_split():
    held_out_items = load_benchmark_split("held_out")
    assert len(held_out_items) == 75

    true_positives = 0
    false_negatives = 0
    false_blocks = 0
    total_compliant = 0

    for item in held_out_items:
        req = AutopsyRequest(
            prompt_text=item["prompt_text"],
            task_type=item["task_family"],
            target_environment="google-antigravity",
        )
        report = await PromptAutopsyEngine.diagnose_prompt(req)
        is_blocked = report.verdict in ("blocked", "needs_revision", "unsuitable")

        if not item["expected_defects"]:
            total_compliant += 1
            if is_blocked:
                false_blocks += 1
        else:
            if item["expected_release_blocked"]:
                if is_blocked:
                    true_positives += 1
                else:
                    false_negatives += 1

    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 1.0
    )
    fp_block_rate = false_blocks / total_compliant if total_compliant > 0 else 0.0

    assert recall >= 0.95, f"Held-out recall below threshold: {recall:.2f}"
    assert fp_block_rate <= 0.05, (
        f"Held-out false-positive block rate exceeded: {fp_block_rate:.2f}"
    )
