"""add subscription plans and business subscriptions

Revision ID: saas2026052401
Revises: dc2026052302
Create Date: 2026-05-24 14:30:00
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from alembic import op
import sqlalchemy as sa


revision = "saas2026052401"
down_revision = "dc2026052302"
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


def _seed_default_subscription_plans() -> None:
    connection = op.get_bind()

    existing_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM subscription_plans")
    ).scalar_one()

    if existing_count > 0:
        return

    now = datetime.now(timezone.utc)

    subscription_plans_table = sa.table(
        "subscription_plans",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("max_users", sa.Integer),
        sa.column("max_managers", sa.Integer),
        sa.column("max_daily_tasks", sa.Integer),
        sa.column("report_retention_days", sa.Integer),
        sa.column("price_monthly", sa.Numeric),
        sa.column("price_yearly", sa.Numeric),
        sa.column("currency", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at_utc", sa.DateTime(timezone=True)),
        sa.column("updated_at_utc", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        subscription_plans_table,
        [
            {
                "code": "trial",
                "name": "Deneme",
                "description": "İlk müşteri denemeleri ve kısa süreli test kullanımı için başlangıç planı.",
                "max_users": 5,
                "max_managers": 1,
                "max_daily_tasks": 100,
                "report_retention_days": 30,
                "price_monthly": Decimal("0.00"),
                "price_yearly": Decimal("0.00"),
                "currency": "TRY",
                "display_order": 10,
                "is_active": True,
                "created_at_utc": now,
                "updated_at_utc": now,
            },
            {
                "code": "starter",
                "name": "Starter",
                "description": "Küçük işletmeler için temel görev ve operasyon yönetimi planı.",
                "max_users": 5,
                "max_managers": 1,
                "max_daily_tasks": 150,
                "report_retention_days": 60,
                "price_monthly": None,
                "price_yearly": None,
                "currency": "TRY",
                "display_order": 20,
                "is_active": True,
                "created_at_utc": now,
                "updated_at_utc": now,
            },
            {
                "code": "standard",
                "name": "Standard",
                "description": "Orta ölçekli ekipler için genişletilmiş kullanıcı ve görev yönetimi planı.",
                "max_users": 15,
                "max_managers": 3,
                "max_daily_tasks": 500,
                "report_retention_days": 90,
                "price_monthly": None,
                "price_yearly": None,
                "currency": "TRY",
                "display_order": 30,
                "is_active": True,
                "created_at_utc": now,
                "updated_at_utc": now,
            },
            {
                "code": "professional",
                "name": "Professional",
                "description": "Yoğun operasyon yöneten işletmeler için profesyonel plan.",
                "max_users": 30,
                "max_managers": 5,
                "max_daily_tasks": 1000,
                "report_retention_days": 180,
                "price_monthly": None,
                "price_yearly": None,
                "currency": "TRY",
                "display_order": 40,
                "is_active": True,
                "created_at_utc": now,
                "updated_at_utc": now,
            },
            {
                "code": "enterprise",
                "name": "Enterprise",
                "description": "Şubeli veya özel ihtiyaçları olan işletmeler için özel teklif planı.",
                "max_users": 9999,
                "max_managers": None,
                "max_daily_tasks": None,
                "report_retention_days": 365,
                "price_monthly": None,
                "price_yearly": None,
                "currency": "TRY",
                "display_order": 50,
                "is_active": True,
                "created_at_utc": now,
                "updated_at_utc": now,
            },
        ],
    )


def upgrade() -> None:
    if not _has_table("subscription_plans"):
        op.create_table(
            "subscription_plans",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("max_users", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("max_managers", sa.Integer(), nullable=True),
            sa.Column("max_daily_tasks", sa.Integer(), nullable=True),
            sa.Column("report_retention_days", sa.Integer(), nullable=False, server_default="60"),
            sa.Column("price_monthly", sa.Numeric(12, 2), nullable=True),
            sa.Column("price_yearly", sa.Numeric(12, 2), nullable=True),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="TRY"),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name="uq_subscription_plans_code"),
        )

    _create_index_if_missing("ix_subscription_plans_id", "subscription_plans", ["id"])
    _create_index_if_missing("ix_subscription_plans_code", "subscription_plans", ["code"])

    _seed_default_subscription_plans()

    if not _has_table("business_subscriptions"):
        op.create_table(
            "business_subscriptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("plan_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="trialing"),
            sa.Column("billing_period", sa.String(length=30), nullable=False, server_default="manual"),
            sa.Column("starts_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ends_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activated_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("suspended_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at_utc", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("max_users_snapshot", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("max_managers_snapshot", sa.Integer(), nullable=True),
            sa.Column("max_daily_tasks_snapshot", sa.Integer(), nullable=True),
            sa.Column("report_retention_days_snapshot", sa.Integer(), nullable=False, server_default="60"),
            sa.Column("price_monthly_snapshot", sa.Numeric(12, 2), nullable=True),
            sa.Column("price_yearly_snapshot", sa.Numeric(12, 2), nullable=True),
            sa.Column("currency_snapshot", sa.String(length=3), nullable=False, server_default="TRY"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
            sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at_utc", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"]),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_business_subscriptions_id", "business_subscriptions", ["id"])
    _create_index_if_missing("ix_business_subscriptions_business_id", "business_subscriptions", ["business_id"])
    _create_index_if_missing("ix_business_subscriptions_plan_id", "business_subscriptions", ["plan_id"])
    _create_index_if_missing("ix_business_subscriptions_status", "business_subscriptions", ["status"])
    _create_index_if_missing("ix_business_subscriptions_ends_at_utc", "business_subscriptions", ["ends_at_utc"])
    _create_index_if_missing("ix_business_subscriptions_is_current", "business_subscriptions", ["is_current"])
    _create_index_if_missing("ix_business_subscriptions_created_by_user_id", "business_subscriptions", ["created_by_user_id"])
    _create_index_if_missing(
        "ix_business_subscriptions_business_current",
        "business_subscriptions",
        ["business_id", "is_current"],
    )
    _create_index_if_missing(
        "ix_business_subscriptions_business_status",
        "business_subscriptions",
        ["business_id", "status"],
    )


def downgrade() -> None:
    if _has_table("business_subscriptions"):
        op.drop_table("business_subscriptions")

    if _has_table("subscription_plans"):
        op.drop_table("subscription_plans")