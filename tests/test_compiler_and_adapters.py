"""Test Target Compilers, Adapters, and Manifest Validation."""

import pytest

from promptiq.adapters import (
    AntigravityTargetAdapter,
    ClaudeCodeTargetAdapter,
    CodexTargetAdapter,
    CursorTargetAdapter,
    GeminiCLITargetAdapter,
    RawPromptTargetAdapter,
)
from promptiq.compiler.pps import PPSBuilder
from promptiq.models.constitution import ProjectConstitution
from promptiq.schemas.pps import TargetProfileSchema


@pytest.fixture
def sample_approved_constitution() -> ProjectConstitution:
    """Fixture returning an approved ProjectConstitution for compilation tests."""
    return ProjectConstitution(
        id="test-const-123",
        project_id="test-proj-456",
        version=1,
        status="approved",
        is_approved=True,
        goals=["Build high-performance message broker in Go"],
        requirements=[
            {
                "id": "REQ-PERF-001",
                "text": "Support 100,000 messages/sec throughput.",
                "category": "performance",
                "priority": "P0",
                "provenance": "user_provided",
                "acceptance_criteria": "Pass load test benchmark",
            },
            {
                "id": "REQ-SEC-002",
                "text": "Authenticate clients via mTLS.",
                "category": "security",
                "priority": "P0",
                "provenance": "user_provided",
                "acceptance_criteria": "Reject unauthenticated TLS handshakes",
            },
        ],
        scope={"in_scope": ["Broker Core", "Metrics"], "out_of_scope": ["Web Dashboard"]},
        ux_specs={},
        technical_direction={"preferred_stack": ["Go", "gRPC"]},
        decisions=[],
        assumptions=[],
        open_questions=[],
    )


def test_antigravity_target_adapter(sample_approved_constitution):
    """Tests compilation into native Google Antigravity plugin bundle."""
    target_prof = TargetProfileSchema(
        host="google-antigravity",
        provider="google",
        model_id="gemini-2.0-flash",
    )
    pps = PPSBuilder.build_from_constitution(sample_approved_constitution, target_prof)
    adapter = AntigravityTargetAdapter()

    manifest, files, warnings = adapter.compile(pps, output_type="complete_package")

    assert manifest["target"] == "google-antigravity"
    assert "plugin.json" in files
    assert "AGENTS.md" in files
    assert "skills/implementation/SKILL.md" in files
    assert "rules/project_invariants.md" in files

    # Verify requirements are preserved
    assert "REQ-PERF-001" in files["AGENTS.md"]
    assert "REQ-SEC-002" in files["AGENTS.md"]


def test_claude_code_target_adapter(sample_approved_constitution):
    """Tests compilation into Claude Code CLAUDE.md."""
    target_prof = TargetProfileSchema(
        host="claude-code",
        provider="anthropic",
        model_id="claude-3-7-sonnet",
    )
    pps = PPSBuilder.build_from_constitution(sample_approved_constitution, target_prof)
    adapter = ClaudeCodeTargetAdapter()

    manifest, files, warnings = adapter.compile(pps, output_type="complete_package")

    assert "CLAUDE.md" in files
    assert ".claude/settings.json" in files
    assert "REQ-PERF-001" in files["CLAUDE.md"]


def test_cursor_target_adapter(sample_approved_constitution):
    """Tests compilation into Cursor .cursorrules and .cursor/rules."""
    target_prof = TargetProfileSchema(
        host="cursor",
        provider="anthropic",
        model_id="claude-3-7-sonnet",
    )
    pps = PPSBuilder.build_from_constitution(sample_approved_constitution, target_prof)
    adapter = CursorTargetAdapter()

    manifest, files, warnings = adapter.compile(pps, output_type="complete_package")

    assert ".cursorrules" in files
    assert ".cursor/rules/requirements.mdc" in files
    assert ".cursor/mcp.json" in files


def test_codex_and_gemini_cli_adapters(sample_approved_constitution):
    """Tests compilation into OpenAI Codex and Gemini CLI formats."""
    target_prof = TargetProfileSchema(host="openai-codex", provider="openai", model_id="gpt-4o")
    pps = PPSBuilder.build_from_constitution(sample_approved_constitution, target_prof)

    codex_adapter = CodexTargetAdapter()
    manifest_codex, files_codex, _ = codex_adapter.compile(pps, output_type="complete_package")
    assert ".well-known/ai-plugin.json" in files_codex

    gemini_adapter = GeminiCLITargetAdapter()
    manifest_gemini, files_gemini, _ = gemini_adapter.compile(pps, output_type="complete_package")
    assert "gemini-extension.json" in files_gemini
    assert "context/instructions.md" in files_gemini


def test_raw_prompt_modes(sample_approved_constitution):
    """Tests raw prompt-only and prompt-suite outputs."""
    target_prof = TargetProfileSchema(host="raw-prompt", provider="generic", model_id="any")
    pps = PPSBuilder.build_from_constitution(sample_approved_constitution, target_prof)
    adapter = RawPromptTargetAdapter()

    # Prompt-only
    _, files_only, _ = adapter.compile(pps, output_type="prompt_only")
    assert "prompt.md" in files_only

    # Prompt-suite
    _, files_suite, _ = adapter.compile(pps, output_type="prompt_suite")
    assert "system_prompt.md" in files_suite
    assert "user_task.md" in files_suite
