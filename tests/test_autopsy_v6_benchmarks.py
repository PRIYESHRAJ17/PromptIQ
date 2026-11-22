"""Evaluation of Prompt Autopsy across development and held-out benchmark splits."""

import json
from pathlib import Path

import pytest

from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.schemas.critic import AutopsyRequest


def load_v6_benchmark():
    fixture_path = Path(__file__).parent / "fixtures" / "autopsy_benchmark_v6.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_autopsy_development_set_metrics():
    """Evaluates precision, recall, and specificity on the development benchmark split."""
    data = load_v6_benchmark()
    dev_set = data["development_set"]

    tp = 0  # True positive: defective prompt correctly flagged with findings
    fp = 0  # False positive: clean prompt incorrectly flagged with blocking findings
    tn = 0  # True negative: clean prompt correctly approved without blocking findings
    fn = 0  # False negative: defective prompt missed

    for item in dev_set:
        req = AutopsyRequest(
            prompt_text=item["prompt_text"],
            task_type=item["task_family"],
            target_environment="google-antigravity",
        )
        resp = await PromptAutopsyEngine.diagnose_prompt(req)

        is_defective = item["expected_category"] is not None
        should_block = item["should_block_release"]

        has_findings = len(resp.findings) > 0
        blocks = resp.verdict == "blocked"

        if is_defective:
            if has_findings:
                tp += 1
            else:
                fn += 1
            # If item expected to block, verify verdict reflects severity
            if should_block:
                assert resp.verdict in ("blocked", "needs_revision"), f"Item {item['id']} failed to block release: {resp.verdict}"
        else:
            # Clean prompt
            if not blocks:
                tn += 1
            else:
                fp += 1

    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * (precision * recall) / max(0.001, precision + recall)

    assert recall >= 0.95, f"Recall too low: {recall:.2f}"
    assert precision >= 0.95, f"Precision too low: {precision:.2f}"
    assert f1 >= 0.95, f"F1 score too low: {f1:.2f}"
    assert fp == 0, f"False positives detected on clean prompts: {fp}"


@pytest.mark.asyncio
async def test_autopsy_held_out_set_generalization():
    """Evaluates generalization and absence of overfitting on the held-out split."""
    data = load_v6_benchmark()
    held_out = data["held_out_set"]

    for item in held_out:
        req = AutopsyRequest(
            prompt_text=item["prompt_text"],
            task_type=item["task_family"],
            target_environment="google-antigravity",
        )
        resp = await PromptAutopsyEngine.diagnose_prompt(req)

        if item["expected_category"] is not None:
            # Defective prompt must be caught
            assert len(resp.findings) > 0, f"Held-out defect {item['id']} was missed!"
            if item["should_block_release"]:
                assert resp.verdict in ("blocked", "needs_revision"), f"Held-out critical {item['id']} did not block!"
        else:
            # Clean prompt must not be blocked
            assert resp.verdict != "blocked", f"Held-out clean prompt {item['id']} falsely blocked!"
