"""Tests for PromptIQ CLI commands."""

from unittest.mock import patch

from promptiq.cli.main import cli_entrypoint


def test_cli_status(capsys):
    with patch("sys.argv", ["promptiq", "status"]):
        cli_entrypoint()

    captured = capsys.readouterr()
    assert "PROMPTIQ CAPACITY & INFERENCE STATUS" in captured.out
    assert "Zero-Price Policy: ACTIVE ($0)" in captured.out


def test_cli_help(capsys):
    with patch("sys.argv", ["promptiq"]):
        cli_entrypoint()

    captured = capsys.readouterr()
    assert "Universal Prompt Intelligence" in captured.out


def test_cli_review_inline_text(capsys):
    with patch(
        "sys.argv", ["promptiq", "review", "Do something useful please", "--target", "claude-code"]
    ):
        cli_entrypoint()

    captured = capsys.readouterr()
    assert "PROMPT AUTOPSY DIAGNOSTIC" in captured.out
    assert "Verdict:" in captured.out
    assert "Findings:" in captured.out


def test_cli_review_file(tmp_path, capsys):
    test_prompt_file = tmp_path / "sample_prompt.txt"
    test_prompt_file.write_text("You are an assistant. Help the user.", encoding="utf-8")

    with patch(
        "sys.argv", ["promptiq", "review", str(test_prompt_file), "--target", "google-antigravity"]
    ):
        cli_entrypoint()

    captured = capsys.readouterr()
    assert "PROMPT AUTOPSY DIAGNOSTIC" in captured.out
    assert "Verdict:" in captured.out
