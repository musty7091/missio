"""add user supervisor relation

Revision ID: team2026053101
Revises: plan2026053001
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "team2026053101"
down_revision = "plan2026053001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("supervisor_user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_users_supervisor_user_id",
        "users",
        ["supervisor_user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_users_supervisor_user_id_users",
        "users",
        "users",
        ["supervisor_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_users_supervisor_user_id_users",
        "users",
        type_="foreignkey",
    )
    op.drop_index("ix_users_supervisor_user_id", table_name="users")
    op.drop_column("users", "supervisor_user_id")
