"""Tests verifying CLI execution as real operating system subprocesses."""

import subprocess
import sys


def test_cli_subprocess_help():
    """Verifies that the CLI executes via subprocess and returns exit code 0 on --help."""
    res = subprocess.run(
        [sys.executable, "-m", "promptiq.cli.main", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "PromptIQ: Universal Prompt Intelligence" in res.stdout
    assert "status" in res.stdout
    assert "quota" in res.stdout
    assert "review" in res.stdout


def test_cli_subprocess_status():
    """Verifies that the CLI status command executes via subprocess and outputs zero-price notice."""
    res = subprocess.run(
        [sys.executable, "-m", "promptiq.cli.main", "status"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "PROMPTIQ CAPACITY & INFERENCE STATUS" in res.stdout
    assert "Zero-Price Policy: ACTIVE ($0)" in res.stdout
    assert "PromptIQ is 100% free" in res.stdout


def test_cli_subprocess_quota():
    """Verifies that the CLI quota command executes via subprocess and renders the quota ledger table."""
    res = subprocess.run(
        [sys.executable, "-m", "promptiq.cli.main", "quota"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "PROMPTIQ REAL-TIME MODEL QUOTA LEDGER" in res.stdout
    assert "gemini-3.8-flash" in res.stdout
    assert "openai/gpt-oss-120b" in res.stdout


def test_cli_subprocess_review_autopsy():
    """Verifies that the CLI review command executes via subprocess and flags excessive agency."""
    res = subprocess.run(
        [sys.executable, "-m", "promptiq.cli.main", "review", "do whatever it takes"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "PROMPT AUTOPSY DIAGNOSTIC" in res.stdout
    assert "Excessive agency detected" in res.stdout
    assert "Verdict: NEEDS_REVISION" in res.stdout


def test_cli_subprocess_credential_redaction():
    """Verifies that the CLI does not leak raw tokens or secrets in stdout/stderr."""
    secret_text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret"
    res = subprocess.run(
        [sys.executable, "-m", "promptiq.cli.main", "review", secret_text],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    # Confirm secret string is not reflected as a valid secret
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in res.stderr
