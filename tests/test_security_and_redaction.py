"""Test Secret Redaction and Input Sanitization."""

from promptiq.core.logging import redact_secrets
from promptiq.core.security import sanitize_untrusted_input


def test_secret_redaction_filters():
    """Verifies that automated redaction strips credentials, API keys, and bearer tokens."""
    sample_log = (
        "User logged in with token Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test and "
        "api_key: AIzaSyD1234567890abcdefghijklmnopqrstuv and Groq key gsk_1234567890abcdefghijklmnopqrstuvwxyz123456"
    )
    redacted = redact_secrets(sample_log)

    assert "eyJhbGci" not in redacted
    assert "AIzaSyD1234567890" not in redacted
    assert "gsk_1234567890" not in redacted
    assert "[REDACTED]" in redacted


def test_input_sanitization():
    """Verifies that non-printable control characters and null bytes are stripped."""
    dirty_input = "Safe command \x00 with null byte and control \x07 character \x1b[31m"
    clean = sanitize_untrusted_input(dirty_input)

    assert "\x00" not in clean
    assert "\x07" not in clean
    assert "Safe command" in clean
