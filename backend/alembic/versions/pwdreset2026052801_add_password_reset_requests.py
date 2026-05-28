"""add password reset requests

Revision ID: pwdreset2026052801
Revises: locchk2026052801
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa


revision = "pwdreset2026052801"
down_revision = "locchk2026052801"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "password_reset_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("requested_username", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("notification_status", sa.String(length=40), nullable=False, server_default="not_attempted"),
        sa.Column("notification_attempted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notification_sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notification_failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_notification_attempt_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_password_reset_requests_business_status", "password_reset_requests", ["business_id", "status"], unique=False)
    op.create_index("ix_password_reset_requests_target_status", "password_reset_requests", ["target_user_id", "status"], unique=False)
    op.create_index("ix_password_reset_requests_requested_at", "password_reset_requests", ["requested_at_utc"], unique=False)
    op.create_index("ix_password_reset_requests_resolved_by", "password_reset_requests", ["resolved_by_user_id"], unique=False)
    op.create_index(op.f("ix_password_reset_requests_business_id"), "password_reset_requests", ["business_id"], unique=False)
    op.create_index(op.f("ix_password_reset_requests_notification_status"), "password_reset_requests", ["notification_status"], unique=False)
    op.create_index(op.f("ix_password_reset_requests_requested_username"), "password_reset_requests", ["requested_username"], unique=False)
    op.create_index(op.f("ix_password_reset_requests_status"), "password_reset_requests", ["status"], unique=False)
    op.create_index(op.f("ix_password_reset_requests_target_user_id"), "password_reset_requests", ["target_user_id"], unique=False)

    if bind.dialect.name != "sqlite":
        op.alter_column(
            "users",
            "must_change_password",
            server_default=None,
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_password_reset_requests_target_user_id"), table_name="password_reset_requests")
    op.drop_index(op.f("ix_password_reset_requests_status"), table_name="password_reset_requests")
    op.drop_index(op.f("ix_password_reset_requests_requested_username"), table_name="password_reset_requests")
    op.drop_index(op.f("ix_password_reset_requests_notification_status"), table_name="password_reset_requests")
    op.drop_index(op.f("ix_password_reset_requests_business_id"), table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_resolved_by", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_requested_at", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_target_status", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_business_status", table_name="password_reset_requests")
    op.drop_table("password_reset_requests")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("must_change_password")