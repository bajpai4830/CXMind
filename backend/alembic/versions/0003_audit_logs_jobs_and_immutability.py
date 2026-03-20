"""audit logs + system jobs + immutability

Revision ID: 0003_audit
Revises: 0002_users
Create Date: 2026-03-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_audit"
down_revision = "0002_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("token_version", sa.Integer(), nullable=False, server_default="1")
        )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)

    op.create_table(
        "system_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_name"),
    )
    op.create_index(op.f("ix_system_jobs_job_name"), "system_jobs", ["job_name"], unique=True)

    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION cxmind_audit_logs_immutable()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'audit_logs is immutable';
            END;
            $$;
            """
        )
        op.execute(
            """
            CREATE TRIGGER cxmind_audit_logs_no_update
            BEFORE UPDATE ON audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION cxmind_audit_logs_immutable();
            """
        )
        op.execute(
            """
            CREATE TRIGGER cxmind_audit_logs_no_delete
            BEFORE DELETE ON audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION cxmind_audit_logs_immutable();
            """
        )
    elif dialect == "sqlite":
        op.execute(
            """
            CREATE TRIGGER cxmind_audit_logs_no_update
            BEFORE UPDATE ON audit_logs
            BEGIN
                SELECT RAISE(ABORT, 'audit_logs is immutable');
            END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER cxmind_audit_logs_no_delete
            BEFORE DELETE ON audit_logs
            BEGIN
                SELECT RAISE(ABORT, 'audit_logs is immutable');
            END;
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS cxmind_audit_logs_no_delete ON audit_logs;")
        op.execute("DROP TRIGGER IF EXISTS cxmind_audit_logs_no_update ON audit_logs;")
        op.execute("DROP FUNCTION IF EXISTS cxmind_audit_logs_immutable();")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS cxmind_audit_logs_no_delete;")
        op.execute("DROP TRIGGER IF EXISTS cxmind_audit_logs_no_update;")

    op.drop_table("system_jobs")
    op.drop_table("audit_logs")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("token_version")

