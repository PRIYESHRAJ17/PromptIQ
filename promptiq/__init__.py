"""PromptIQ: Universal Prompt Intelligence, Project Engineering and Cross-Agent Continuity Platform."""

import os

# Guarantee Windows Smart App Control compatibility and portable execution across environments
# by enforcing pure-Python fallbacks for compiled C-extensions.
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

__version__ = "0.2.0"
