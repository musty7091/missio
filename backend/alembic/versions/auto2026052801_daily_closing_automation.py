"""add automatic daily closing settings

Revision ID: auto2026052801
Revises: webpush2026052501
Create Date: 2026-05-28 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "auto2026052801"
down_revision = "webpush2026052501"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("businesses", "auto_daily_closing_enabled"):
        op.add_column(
            "businesses",
            sa.Column(
                "auto_daily_closing_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    if not _has_column("businesses", "daily_closing_time"):
        op.add_column(
            "businesses",
            sa.Column(
                "daily_closing_time",
                sa.String(length=5),
                nullable=False,
                server_default="23:45",
            ),
        )

    if not _has_column("daily_operation_closures", "closed_by_system"):
        op.add_column(
            "daily_operation_closures",
            sa.Column(
                "closed_by_system",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    with op.batch_alter_table("daily_operation_closures") as batch_op:
        batch_op.alter_column(
            "closed_by_user_id",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("daily_operation_closures") as batch_op:
        batch_op.alter_column(
            "closed_by_user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    if _has_column("daily_operation_closures", "closed_by_system"):
        op.drop_column("daily_operation_closures", "closed_by_system")

    if _has_column("businesses", "daily_closing_time"):
        op.drop_column("businesses", "daily_closing_time")

    if _has_column("businesses", "auto_daily_closing_enabled"):
        op.drop_column("businesses", "auto_daily_closing_enabled")
