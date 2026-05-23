"""add daily operation closure tables

Revision ID: dc2026052302
Revises: b4f1c9d8a2e3
Create Date: 2026-05-23 18:36:27
"""

from alembic import op
import sqlalchemy as sa


revision = "dc2026052302"
down_revision = "b4f1c9d8a2e3"
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
    if not _has_table("daily_operation_closures"):
        op.create_table(
            "daily_operation_closures",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("closure_date", sa.Date(), nullable=False),
            sa.Column("closed_by_user_id", sa.Integer(), nullable=False),
            sa.Column("closed_by_user_full_name", sa.String(length=200), nullable=False),
            sa.Column("closed_by_username", sa.String(length=100), nullable=False),
            sa.Column("closed_by_role", sa.String(length=50), nullable=False),
            sa.Column("closed_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("manager_note", sa.Text(), nullable=True),
            sa.Column("total_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completed_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("approved_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("open_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("rejected_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("approval_pending_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("photo_required_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("photo_evidence_task_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "business_id",
                "closure_date",
                name="uq_daily_operation_closures_business_date",
            ),
        )

    _create_index_if_missing("ix_daily_operation_closures_id", "daily_operation_closures", ["id"])
    _create_index_if_missing("ix_daily_operation_closures_business_id", "daily_operation_closures", ["business_id"])
    _create_index_if_missing("ix_daily_operation_closures_closure_date", "daily_operation_closures", ["closure_date"])
    _create_index_if_missing("ix_daily_operation_closures_closed_by_user_id", "daily_operation_closures", ["closed_by_user_id"])
    _create_index_if_missing("ix_daily_operation_closures_status", "daily_operation_closures", ["status"])

    if not _has_table("daily_operation_closure_items"):
        op.create_table(
            "daily_operation_closure_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("closure_id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("task_date", sa.Date(), nullable=False),
            sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
            sa.Column("assigned_to_user_full_name", sa.String(length=200), nullable=True),
            sa.Column("assigned_to_username", sa.String(length=100), nullable=True),
            sa.Column("task_title", sa.String(length=200), nullable=False),
            sa.Column("task_description", sa.Text(), nullable=True),
            sa.Column("task_type", sa.String(length=30), nullable=False),
            sa.Column("task_status", sa.String(length=50), nullable=False),
            sa.Column("task_priority", sa.String(length=30), nullable=False),
            sa.Column("requires_photo", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("requires_location", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("requires_manager_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("has_photo_evidence", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("assigned_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.ForeignKeyConstraint(["closure_id"], ["daily_operation_closures.id"]),
            sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "closure_id",
                "task_id",
                name="uq_daily_operation_closure_items_closure_task",
            ),
        )

    _create_index_if_missing("ix_daily_operation_closure_items_id", "daily_operation_closure_items", ["id"])
    _create_index_if_missing("ix_daily_operation_closure_items_closure_id", "daily_operation_closure_items", ["closure_id"])
    _create_index_if_missing("ix_daily_operation_closure_items_business_id", "daily_operation_closure_items", ["business_id"])
    _create_index_if_missing("ix_daily_operation_closure_items_task_id", "daily_operation_closure_items", ["task_id"])
    _create_index_if_missing("ix_daily_operation_closure_items_task_date", "daily_operation_closure_items", ["task_date"])
    _create_index_if_missing("ix_daily_operation_closure_items_assigned_to_user_id", "daily_operation_closure_items", ["assigned_to_user_id"])
    _create_index_if_missing("ix_daily_operation_closure_items_task_status", "daily_operation_closure_items", ["task_status"])


def downgrade() -> None:
    if _has_table("daily_operation_closure_items"):
        op.drop_index("ix_daily_operation_closure_items_task_status", table_name="daily_operation_closure_items")
        op.drop_index("ix_daily_operation_closure_items_assigned_to_user_id", table_name="daily_operation_closure_items")
        op.drop_index("ix_daily_operation_closure_items_task_date", table_name="daily_operation_closure_items")
        op.drop_index("ix_daily_operation_closure_items_task_id", table_name="daily_operation_closure_items")
        op.drop_index("ix_daily_operation_closure_items_business_id", table_name="daily_operation_closure_items")
        op.drop_index("ix_daily_operation_closure_items_closure_id", table_name="daily_operation_closure_items")
        op.drop_index("ix_daily_operation_closure_items_id", table_name="daily_operation_closure_items")
        op.drop_table("daily_operation_closure_items")

    if _has_table("daily_operation_closures"):
        op.drop_index("ix_daily_operation_closures_status", table_name="daily_operation_closures")
        op.drop_index("ix_daily_operation_closures_closed_by_user_id", table_name="daily_operation_closures")
        op.drop_index("ix_daily_operation_closures_closure_date", table_name="daily_operation_closures")
        op.drop_index("ix_daily_operation_closures_business_id", table_name="daily_operation_closures")
        op.drop_index("ix_daily_operation_closures_id", table_name="daily_operation_closures")
        op.drop_table("daily_operation_closures")

