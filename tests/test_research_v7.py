"""Tests for PromptIQ Research Quality, Claim Verification, and Untrusted Isolation."""

import json
from pathlib import Path

from promptiq.research.evidence_graph import (
    ClaimSupportClassification,
    EvidenceGraphBuilder,
    SourceReliabilityTier,
)

BENCHMARK_PATH = Path("tests/fixtures/research_benchmark_v7.json")


def load_research_benchmark():
    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        return json.load(f)["cases"]


def test_research_benchmark_dataset_integrity():
    cases = load_research_benchmark()
    assert len(cases) == 100
    held_out = [c for c in cases if c["is_held_out"]]
    dev_set = [c for c in cases if not c["is_held_out"]]
    assert len(held_out) == 50
    assert len(dev_set) == 50


def test_independent_claim_support_verification():
    cases = load_research_benchmark()
    correct_count = 0
    total = len(cases)

    for case in cases:
        claim_id = case["case_id"]
        claim_text = case["claim"]
        excerpt_text = case["excerpt"]
        expected_cls = case["expected_classification"]

        res = EvidenceGraphBuilder.verify_claim_support(
            claim_id=claim_id,
            claim_text=claim_text,
            excerpt_text=excerpt_text,
        )

        assert res.classification in [c.value for c in ClaimSupportClassification]

        # Check classification accuracy
        if res.classification == expected_cls:
            correct_count += 1

    accuracy = correct_count / total
    # Verify overall classification accuracy exceeds 90% threshold
    assert accuracy >= 0.90, f"Expected accuracy >= 0.90, got {accuracy:.2f}"


def test_prompt_injection_sanitization_defense():
    cases = load_research_benchmark()
    injection_cases = [c for c in cases if c["contains_prompt_injection"]]
    assert len(injection_cases) == 10

    for case in injection_cases:
        raw_excerpt = case["excerpt"]
        sanitized = EvidenceGraphBuilder.sanitize_untrusted_content(raw_excerpt)
        assert "System Override" not in sanitized
        assert "Ignore previous instructions" not in sanitized
        assert "[SANITIZED_PROMPT_INJECTION_ATTEMPT]" in sanitized


def test_exact_character_offset_citation_verification():
    source_document = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python. "
        "It supports asynchronous programming natively using async and await syntax."
    )
    target_phrase = "supports asynchronous programming natively"

    excerpt = EvidenceGraphBuilder.extract_verifiable_excerpt(
        source_body=source_document,
        target_phrase=target_phrase,
        source_url="https://fastapi.tiangolo.com",
        source_title="FastAPI Documentation",
        publisher="Tiangolo",
        reliability_tier=SourceReliabilityTier.TIER_1_PRIMARY,
    )

    assert excerpt is not None
    assert excerpt.text_excerpt == target_phrase
    assert excerpt.start_offset >= 0
    assert excerpt.end_offset > excerpt.start_offset

    # Verify citation matches exact offsets
    verified = EvidenceGraphBuilder.verify_citation(excerpt, source_document)
    assert verified is True

    # Negative test: offset mismatch
    excerpt.start_offset += 5
    mismatched = EvidenceGraphBuilder.verify_citation(excerpt, source_document)
    assert mismatched is False
