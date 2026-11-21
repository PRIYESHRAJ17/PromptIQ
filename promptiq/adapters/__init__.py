"""Target adapters module."""

from promptiq.adapters.antigravity import AntigravityTargetAdapter
from promptiq.adapters.base import BaseTargetAdapter
from promptiq.adapters.claude import ClaudeCodeTargetAdapter
from promptiq.adapters.codex import CodexTargetAdapter
from promptiq.adapters.cursor import CursorTargetAdapter
from promptiq.adapters.gemini import GeminiCLITargetAdapter
from promptiq.adapters.raw_prompt import RawPromptTargetAdapter

__all__ = [
    "BaseTargetAdapter",
    "AntigravityTargetAdapter",
    "ClaudeCodeTargetAdapter",
    "CursorTargetAdapter",
    "CodexTargetAdapter",
    "GeminiCLITargetAdapter",
    "RawPromptTargetAdapter",
]
