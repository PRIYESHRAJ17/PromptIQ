"""Structured logging with automated secret redaction for PromptIQ."""

import json
import logging
import re
import sys
from typing import Any

from promptiq.core.config import settings

# Patterns for sensitive tokens, API keys, passwords, and authorization headers
SECRET_PATTERNS = [
    re.compile(r"Bearer\s+([A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*)", re.IGNORECASE),
    re.compile(r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?", re.IGNORECASE),
    re.compile(r"(AIza[0-9A-Za-z-_]{35})"),       # Google API Key
    re.compile(r"(gsk_[A-Za-z0-9]{48,})"),        # Groq API Key
    re.compile(r"(sk-[A-Za-z0-9]{32,})"),         # OpenAI/generic secret key
    re.compile(r"(ghp_[A-Za-z0-9]{36})"),         # GitHub personal access token
]


def redact_secrets(text: str) -> str:
    """Scrub sensitive credentials, tokens, and keys from text."""
    if not isinstance(text, str):
        return text
    redacted = text

    # Bearer token
    redacted = re.sub(
        r"Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*",
        "Bearer [REDACTED]",
        redacted,
        flags=re.IGNORECASE,
    )

    # API keys and secrets with key name
    redacted = re.sub(
        r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?",
        r"\1: [REDACTED]",
        redacted,
        flags=re.IGNORECASE,
    )

    # Google API Key
    redacted = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED]", redacted)

    # Groq API Key
    redacted = re.sub(r"gsk_[A-Za-z0-9]{40,}", "[REDACTED]", redacted)

    # OpenAI / generic secret key
    redacted = re.sub(r"sk-[A-Za-z0-9]{32,}", "[REDACTED]", redacted)

    # GitHub personal access token
    redacted = re.sub(r"ghp_[A-Za-z0-9]{36}", "[REDACTED]", redacted)

    return redacted


class RedactingJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON while scrubbing sensitive data."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_secrets(record.getMessage()),
        }

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data["extra"] = {
                k: redact_secrets(str(v)) if isinstance(v, str) else v
                for k, v in record.extra.items()
            }

        if record.exc_info:
            log_data["exception"] = redact_secrets(self.formatException(record.exc_info))

        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """Configures the root and promptiq loggers."""
    log_level = getattr(logging, settings.PROMPTIQ_LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger("promptiq")
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if already configured
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(RedactingJsonFormatter())
        root_logger.addHandler(handler)

    return root_logger


logger = setup_logging()
