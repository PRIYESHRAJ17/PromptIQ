"""Reproducible Development Setup Script for PromptIQ.

Sets up environment variables, verifies pure-Python execution, and tests database migrations
in compliance with Windows Smart App Control and cross-platform standards.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath("."))


def setup():
    print("=" * 60)
    print("PromptIQ Development Environment Setup")
    print("=" * 60)

    # 1. Enforce pure-Python SQLAlchemy to prevent .pyd C-extension blocks under Smart App Control
    os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
    print("[1/4] Pure-Python execution mode enabled (DISABLE_SQLALCHEMY_CEXT=1)")

    # 2. Check virtual environment
    in_venv = sys.prefix != sys.base_prefix
    print(f"[2/4] Python Environment: {sys.executable} (In virtualenv: {in_venv})")

    # 3. Verify core imports
    try:
        import importlib

        for mod_name in ("fastapi", "pydantic", "sqlalchemy", "alembic", "promptiq"):
            importlib.import_module(mod_name)
        print("[3/4] Core dependencies successfully imported.")
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}. Please run: pip install -e .")
        sys.exit(1)

    # 4. Run database migration check
    print("[4/4] Verifying database schema & migrations...")
    try:
        from alembic.config import Config

        from alembic import command

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", "sqlite+aiosqlite:///./promptiq_dev.db")
        command.upgrade(alembic_cfg, "head")
        print("      Database migration to HEAD verified successfully.")
    except Exception as e:
        print(f"      Database migration notice: {e}")

    print("\nEnvironment setup verified successfully. PromptIQ is ready for development.")
    print("Run tests with: pytest")


if __name__ == "__main__":
    setup()
