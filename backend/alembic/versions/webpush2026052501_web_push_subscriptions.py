"""add web push subscriptions

Revision ID: webpush2026052501
Revises: push2026052401
Create Date: 2026-05-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "webpush2026052501"
down_revision = "push2026052401"
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
    if not _has_table("web_push_subscriptions"):
        op.create_table(
            "web_push_subscriptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("endpoint", sa.Text(), nullable=False),
            sa.Column("endpoint_hash", sa.String(length=128), nullable=False),
            sa.Column("p256dh_key", sa.Text(), nullable=False),
            sa.Column("auth_key", sa.Text(), nullable=False),
            sa.Column("content_encoding", sa.String(length=30), nullable=False, server_default="aes128gcm"),
            sa.Column("device_type", sa.String(length=60), nullable=True),
            sa.Column("browser_name", sa.String(length=120), nullable=True),
            sa.Column("platform", sa.String(length=120), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("expiration_time_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("last_seen_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_web_push_subscriptions_id", "web_push_subscriptions", ["id"])
    _create_index_if_missing("ix_web_push_subscriptions_business_id", "web_push_subscriptions", ["business_id"])
    _create_index_if_missing("ix_web_push_subscriptions_user_id", "web_push_subscriptions", ["user_id"])
    _create_index_if_missing("ix_web_push_subscriptions_endpoint_hash", "web_push_subscriptions", ["endpoint_hash"])
    _create_index_if_missing("ix_web_push_subscriptions_is_active", "web_push_subscriptions", ["is_active"])
    _create_index_if_missing(
        "ix_web_push_subscriptions_user_active",
        "web_push_subscriptions",
        ["user_id", "is_active"],
    )
    _create_index_if_missing(
        "ix_web_push_subscriptions_business_active",
        "web_push_subscriptions",
        ["business_id", "is_active"],
    )
    _create_index_if_missing(
        "ix_web_push_subscriptions_endpoint_active",
        "web_push_subscriptions",
        ["endpoint_hash", "is_active"],
    )


def downgrade() -> None:
    if _has_table("web_push_subscriptions"):
        op.drop_table("web_push_subscriptions")
