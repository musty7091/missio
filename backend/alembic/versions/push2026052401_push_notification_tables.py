"""add push notification tables

Revision ID: push2026052401
Revises: saas2026052401
Create Date: 2026-05-24 19:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "push2026052401"
down_revision = "saas2026052401"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return inspector.has_table(table_name)


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    if not _has_table("push_notification_tokens"):
        op.create_table(
            "push_notification_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("fcm_token", sa.Text(), nullable=False),
            sa.Column("device_type", sa.String(length=60), nullable=True),
            sa.Column("browser_name", sa.String(length=120), nullable=True),
            sa.Column("platform", sa.String(length=120), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("last_seen_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("fcm_token", name="uq_push_notification_tokens_fcm_token"),
        )

    _create_index_if_missing("ix_push_notification_tokens_id", "push_notification_tokens", ["id"])
    _create_index_if_missing("ix_push_notification_tokens_business_id", "push_notification_tokens", ["business_id"])
    _create_index_if_missing("ix_push_notification_tokens_user_id", "push_notification_tokens", ["user_id"])
    _create_index_if_missing("ix_push_notification_tokens_is_active", "push_notification_tokens", ["is_active"])
    _create_index_if_missing(
        "ix_push_notification_tokens_user_active",
        "push_notification_tokens",
        ["user_id", "is_active"],
    )
    _create_index_if_missing(
        "ix_push_notification_tokens_business_active",
        "push_notification_tokens",
        ["business_id", "is_active"],
    )

    if not _has_table("push_notification_logs"):
        op.create_table(
            "push_notification_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("token_id", sa.Integer(), nullable=True),
            sa.Column("notification_type", sa.String(length=80), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("data_json", sa.Text(), nullable=True),
            sa.Column("fcm_message_id", sa.String(length=500), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("sent_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["token_id"], ["push_notification_tokens.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_push_notification_logs_id", "push_notification_logs", ["id"])
    _create_index_if_missing("ix_push_notification_logs_business_id", "push_notification_logs", ["business_id"])
    _create_index_if_missing("ix_push_notification_logs_user_id", "push_notification_logs", ["user_id"])
    _create_index_if_missing("ix_push_notification_logs_token_id", "push_notification_logs", ["token_id"])
    _create_index_if_missing("ix_push_notification_logs_notification_type", "push_notification_logs", ["notification_type"])
    _create_index_if_missing("ix_push_notification_logs_status", "push_notification_logs", ["status"])
    _create_index_if_missing(
        "ix_push_notification_logs_business_type",
        "push_notification_logs",
        ["business_id", "notification_type"],
    )
    _create_index_if_missing(
        "ix_push_notification_logs_user_status",
        "push_notification_logs",
        ["user_id", "status"],
    )


def downgrade() -> None:
    if _has_table("push_notification_logs"):
        op.drop_table("push_notification_logs")

    if _has_table("push_notification_tokens"):
        op.drop_table("push_notification_tokens")
