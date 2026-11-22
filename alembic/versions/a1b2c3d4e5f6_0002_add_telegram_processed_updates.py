"""0002_add_telegram_processed_updates

Revision ID: a1b2c3d4e5f6
Revises: 823672db2f75
Create Date: 2026-11-22 09:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "823672db2f75"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include telegram_processed_updates table."""
    op.create_table(
        "telegram_processed_updates",
        sa.Column("update_id", sa.BigInteger(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("update_id"),
    )
    with op.batch_alter_table("telegram_processed_updates", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_telegram_processed_updates_update_id"),
            ["update_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema to remove telegram_processed_updates table."""
    with op.batch_alter_table("telegram_processed_updates", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_telegram_processed_updates_update_id"))
    op.drop_table("telegram_processed_updates")
