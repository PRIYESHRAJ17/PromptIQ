"""Test Database Migrations and Schema Upgrades."""

from pathlib import Path

from alembic.config import Config

from alembic import command


def test_alembic_upgrade_and_downgrade():
    """Verifies that Alembic migration upgrade to head and downgrade to base succeed cleanly."""
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    assert alembic_ini_path.exists(), "alembic.ini must exist at workspace root"

    alembic_cfg = Config(str(alembic_ini_path))
    # Use in-memory SQLite database URL for isolation during migration test
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite+aiosqlite:///./test_migration.db")

    # Run upgrade head
    command.upgrade(alembic_cfg, "head")

    # Run downgrade base
    command.downgrade(alembic_cfg, "base")

    # Re-run upgrade head
    command.upgrade(alembic_cfg, "head")

    # Cleanup test db file
    test_db = Path("./test_migration.db")
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass
