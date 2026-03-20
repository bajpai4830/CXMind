"""org id isolation

Revision ID: 0004_org_id
Revises: 0003_audit
Create Date: 2026-03-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004_org_id"
down_revision = "0003_audit"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # 2. Insert a default org
    op.execute(
        "INSERT INTO organizations (id, name, created_at) VALUES (1, 'Default Organization', NOW())"
    )
    
    # 3. ADD COLUMN org_id INTEGER DEFAULT 1 (backfills existing rows)
    op.add_column("users", sa.Column("org_id", sa.Integer(), server_default=sa.text("1"), nullable=False))
    op.create_index(op.f("ix_users_org_id"), "users", ["org_id"], unique=False)
    
    op.add_column("customers", sa.Column("org_id", sa.Integer(), server_default=sa.text("1"), nullable=False))
    op.create_index(op.f("ix_customers_org_id"), "customers", ["org_id"], unique=False)
    
    op.add_column("interactions", sa.Column("org_id", sa.Integer(), server_default=sa.text("1"), nullable=False))
    op.create_index(op.f("ix_interactions_org_id"), "interactions", ["org_id"], unique=False)
    
    # 4. Add Foreign Key constraint AFTER backfill
    op.create_foreign_key("fk_users_org_id", "users", "organizations", ["org_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_customers_org_id", "customers", "organizations", ["org_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_interactions_org_id", "interactions", "organizations", ["org_id"], ["id"], ondelete="CASCADE")
    
    # 5. Remove DEFAULT, make it required going forward
    op.alter_column("users", "org_id", server_default=None)
    op.alter_column("customers", "org_id", server_default=None)
    op.alter_column("interactions", "org_id", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_interactions_org_id", "interactions", type_="foreignkey")
    op.drop_index(op.f("ix_interactions_org_id"), table_name="interactions")
    op.drop_column("interactions", "org_id")
    
    op.drop_constraint("fk_customers_org_id", "customers", type_="foreignkey")
    op.drop_index(op.f("ix_customers_org_id"), table_name="customers")
    op.drop_column("customers", "org_id")
    
    op.drop_constraint("fk_users_org_id", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_org_id"), table_name="users")
    op.drop_column("users", "org_id")
    
    op.drop_table("organizations")
