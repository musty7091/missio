"""add manual location checks

Revision ID: locchk2026052801
Revises: auto2026052801
Create Date: 2026-05-28 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "locchk2026052801"
down_revision = "auto2026052801"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return inspector.has_table(table_name)


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    if not _has_table("location_checks"):
        op.create_table(
            "location_checks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("request_group_id", sa.String(length=64), nullable=True),
            sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
            sa.Column("target_user_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
            sa.Column("request_note", sa.Text(), nullable=True),
            sa.Column(
                "notification_status",
                sa.String(length=40),
                nullable=False,
                server_default="not_attempted",
            ),
            sa.Column(
                "notification_attempted_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "notification_sent_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "notification_failed_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column("last_notification_attempt_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("staff_seen_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("responded_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("location_accuracy", sa.Float(), nullable=True),
            sa.Column("response_error_code", sa.String(length=80), nullable=True),
            sa.Column("response_error_message", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(length=100), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("requested_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_location_checks_id", "location_checks", ["id"])
    _create_index_if_missing("ix_location_checks_business_id", "location_checks", ["business_id"])
    _create_index_if_missing("ix_location_checks_request_group_id", "location_checks", ["request_group_id"])
    _create_index_if_missing(
        "ix_location_checks_requested_by_user_id",
        "location_checks",
        ["requested_by_user_id"],
    )
    _create_index_if_missing("ix_location_checks_target_user_id", "location_checks", ["target_user_id"])
    _create_index_if_missing("ix_location_checks_status", "location_checks", ["status"])
    _create_index_if_missing(
        "ix_location_checks_notification_status",
        "location_checks",
        ["notification_status"],
    )
    _create_index_if_missing(
        "ix_location_checks_requested_at",
        "location_checks",
        ["requested_at_utc"],
    )
    _create_index_if_missing(
        "ix_location_checks_business_status",
        "location_checks",
        ["business_id", "status"],
    )
    _create_index_if_missing(
        "ix_location_checks_target_status",
        "location_checks",
        ["target_user_id", "status"],
    )
    _create_index_if_missing(
        "ix_location_checks_request_group",
        "location_checks",
        ["request_group_id"],
    )


def downgrade() -> None:
    if _has_table("location_checks"):
        op.drop_table("location_checks")
