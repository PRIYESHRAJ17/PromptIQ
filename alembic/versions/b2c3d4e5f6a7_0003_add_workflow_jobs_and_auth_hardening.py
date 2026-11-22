"""0003_add_workflow_jobs_and_auth_hardening

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-22 11:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema with workflow_jobs, revoked_tokens, refresh_tokens, and quota_ledger_entries."""
    # 1. workflow_jobs table
    op.create_table(
        "workflow_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("operation_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=True),
        sa.Column("stage_history", sa.JSON(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("execution_provenance", sa.JSON(), nullable=False),
        sa.Column("checkpoint_data", sa.JSON(), nullable=False),
        sa.Column("result_data", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("lease_owner", sa.String(length=64), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fencing_token", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("workflow_jobs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_workflow_jobs_user_id"), ["user_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_workflow_jobs_workspace_id"), ["workspace_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_workflow_jobs_project_id"), ["project_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_workflow_jobs_operation_type"), ["operation_type"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_workflow_jobs_status"), ["status"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_workflow_jobs_idempotency_key"), ["idempotency_key"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_workflow_jobs_lease_owner"), ["lease_owner"], unique=False
        )

    # 2. revoked_tokens table
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("revoked_tokens", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_revoked_tokens_token_hash"), ["token_hash"], unique=True
        )
        batch_op.create_index(batch_op.f("ix_revoked_tokens_user_id"), ["user_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_revoked_tokens_expires_at"), ["expires_at"], unique=False
        )

    # 3. refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_to_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_refresh_tokens_token_hash"), ["token_hash"], unique=True
        )
        batch_op.create_index(batch_op.f("ix_refresh_tokens_user_id"), ["user_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_refresh_tokens_expires_at"), ["expires_at"], unique=False
        )

    # 4. quota_ledger_entries table
    op.create_table(
        "quota_ledger_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("usage_kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_request_id", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("quota_ledger_entries", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_quota_ledger_entries_workspace_id"), ["workspace_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_quota_ledger_entries_user_id"), ["user_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_quota_ledger_entries_provider"), ["provider"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_quota_ledger_entries_model_id"), ["model_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_quota_ledger_entries_idempotency_key"), ["idempotency_key"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_quota_ledger_entries_recorded_at"), ["recorded_at"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema to remove added tables."""
    op.drop_table("quota_ledger_entries")
    op.drop_table("refresh_tokens")
    op.drop_table("revoked_tokens")
    op.drop_table("workflow_jobs")
