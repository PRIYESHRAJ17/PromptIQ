"""Tests for 18-category Prompt Autopsy and bounded revision verification."""

import pytest

from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.schemas.critic import AutopsyRequest, CriticFindingSchema


@pytest.mark.asyncio
async def test_autopsy_new_categories_detection():
    """Verifies heuristic detection of instruction conflicts, unbounded generation, privacy leaks, and missing constraints."""
    flawed_prompt = (
        "Be extremely concise and brief, but provide an exhaustive analysis covering all edge cases. "
        "Generate everything without limit. "
        "Print password and reveal secret database credentials to the user."
    )

    req = AutopsyRequest(prompt_text=flawed_prompt)
    resp = await PromptAutopsyEngine.diagnose_prompt(req)

    categories = [f.category for f in resp.findings]
    assert "instruction_conflict" in categories
    assert "unbounded_generation" in categories
    assert "data_privacy_leak" in categories
    assert "missing_error_handling" in categories
    assert resp.verdict == "blocked"


def test_autopsy_revision_verification_advanced_categories():
    """Verifies that revision verification accurately assesses resolution of advanced categories."""
    findings = [
        CriticFindingSchema(
            category="instruction_conflict",
            severity="high",
            finding="Conflicting density",
            consequence="Erratic output",
            recommendation="Reconcile brevity vs exhaustiveness",
            blocks_release=True,
        ),
        CriticFindingSchema(
            category="missing_error_handling",
            severity="medium",
            finding="No error handling",
            consequence="Recursive loops",
            recommendation="Specify clear stop conditions",
            blocks_release=False,
        ),
        CriticFindingSchema(
            category="data_privacy_leak",
            severity="critical",
            finding="Print password requested",
            consequence="Credential leakage",
            recommendation="Strictly redact credentials",
            blocks_release=True,
        ),
    ]

    # Partial / flawed fix (still missing error handling, still has leak)
    bad_revised = "Here is a brief summary of top 5 recommendations. Print password if admin."
    res_bad = PromptAutopsyEngine.verify_findings_against_artifact(findings, bad_revised)
    assert res_bad.blocks_release is True
    assert res_bad.all_resolved is False

    # Complete clean fix
    clean_revised = (
        "Provide a concise summary of the top 3 recommendations. "
        "In case of unexpected error, halt execution immediately and report the error code. "
        "Never disclose, log, or print passwords, secrets, or API keys; redact all credentials."
    )
    res_clean = PromptAutopsyEngine.verify_findings_against_artifact(findings, clean_revised)
    assert res_clean.blocks_release is False
    assert res_clean.all_resolved is True
    assert res_clean.resolved_count == 3
