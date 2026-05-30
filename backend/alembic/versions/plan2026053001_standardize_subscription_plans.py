"""standardize subscription plans

Revision ID: plan2026053001
Revises: auto2026052801
Create Date: 2026-05-30 22:30:00
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from alembic import op
import sqlalchemy as sa


revision = "plan2026053001"
down_revision = "pwdreset2026052801"
branch_labels = None
depends_on = None


CANONICAL_PLAN_CODES = (
    "trial",
    "starter",
    "professional",
    "enterprise",
)

CANONICAL_PLANS = [
    {
        "code": "trial",
        "name": "Trial",
        "description": "14 günlük deneme kullanımı için ücretsiz plan.",
        "max_users": 10,
        "max_managers": 2,
        "max_daily_tasks": 200,
        "report_retention_days": 14,
        "price_monthly": Decimal("0.00"),
        "price_yearly": Decimal("0.00"),
        "currency": "TRY",
        "display_order": 10,
        "is_active": True,
    },
    {
        "code": "starter",
        "name": "Başlangıç",
        "description": "Küçük ekipler için temel Missio planı.",
        "max_users": 10,
        "max_managers": 2,
        "max_daily_tasks": 200,
        "report_retention_days": 14,
        "price_monthly": Decimal("1000.00"),
        "price_yearly": Decimal("10000.00"),
        "currency": "TRY",
        "display_order": 20,
        "is_active": True,
    },
    {
        "code": "professional",
        "name": "Profesyonel",
        "description": "Orta ölçekli operasyon ekipleri için profesyonel Missio planı.",
        "max_users": 25,
        "max_managers": 5,
        "max_daily_tasks": 500,
        "report_retention_days": 14,
        "price_monthly": Decimal("2500.00"),
        "price_yearly": Decimal("25000.00"),
        "currency": "TRY",
        "display_order": 30,
        "is_active": True,
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "description": "Daha büyük operasyon ekipleri için Enterprise Missio planı.",
        "max_users": 50,
        "max_managers": 10,
        "max_daily_tasks": 1000,
        "report_retention_days": 14,
        "price_monthly": Decimal("5000.00"),
        "price_yearly": Decimal("50000.00"),
        "currency": "TRY",
        "display_order": 40,
        "is_active": True,
    },
]

# Eski plan kodları artık sistemde kalmayacak.
# Bu kodlara bağlı abonelikler önce yeni 4'lü yapıya taşınır, sonra eski plan satırları silinir.
LEGACY_PLAN_TARGETS = {
    "standard": "professional",
    "business": "professional",
    "pro": "enterprise",
    "demo": "trial",
    "default": "starter",
    "basic": "starter",
}


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return inspector.has_table(table_name)


def _get_plan_by_code(connection, code: str):
    return (
        connection.execute(
            sa.text(
                """
                SELECT
                    id,
                    code,
                    max_users,
                    max_managers,
                    max_daily_tasks,
                    report_retention_days,
                    price_monthly,
                    price_yearly,
                    currency
                FROM subscription_plans
                WHERE code = :code
                """
            ),
            {"code": code},
        )
        .mappings()
        .one_or_none()
    )


def _upsert_plan(connection, plan: dict[str, object], now) -> None:
    existing_plan = _get_plan_by_code(connection, str(plan["code"]))

    parameters = {
        **plan,
        "now": now,
    }

    if existing_plan is None:
        connection.execute(
            sa.text(
                """
                INSERT INTO subscription_plans (
                    code,
                    name,
                    description,
                    max_users,
                    max_managers,
                    max_daily_tasks,
                    report_retention_days,
                    price_monthly,
                    price_yearly,
                    currency,
                    display_order,
                    is_active,
                    created_at_utc,
                    updated_at_utc
                ) VALUES (
                    :code,
                    :name,
                    :description,
                    :max_users,
                    :max_managers,
                    :max_daily_tasks,
                    :report_retention_days,
                    :price_monthly,
                    :price_yearly,
                    :currency,
                    :display_order,
                    :is_active,
                    :now,
                    :now
                )
                """
            ),
            parameters,
        )
        return

    connection.execute(
        sa.text(
            """
            UPDATE subscription_plans
            SET
                name = :name,
                description = :description,
                max_users = :max_users,
                max_managers = :max_managers,
                max_daily_tasks = :max_daily_tasks,
                report_retention_days = :report_retention_days,
                price_monthly = :price_monthly,
                price_yearly = :price_yearly,
                currency = :currency,
                display_order = :display_order,
                is_active = :is_active,
                updated_at_utc = :now
            WHERE code = :code
            """
        ),
        parameters,
    )


def _sync_subscription_snapshots_for_plan(connection, plan_code: str) -> None:
    plan = _get_plan_by_code(connection, plan_code)

    if plan is None:
        raise RuntimeError(f"Plan bulunamadı: {plan_code}")

    connection.execute(
        sa.text(
            """
            UPDATE business_subscriptions
            SET
                max_users_snapshot = :max_users,
                max_managers_snapshot = :max_managers,
                max_daily_tasks_snapshot = :max_daily_tasks,
                report_retention_days_snapshot = :report_retention_days,
                price_monthly_snapshot = :price_monthly,
                price_yearly_snapshot = :price_yearly,
                currency_snapshot = :currency,
                updated_at_utc = :now
            WHERE plan_id = :plan_id
            """
        ),
        {
            "plan_id": plan["id"],
            "max_users": plan["max_users"],
            "max_managers": plan["max_managers"],
            "max_daily_tasks": plan["max_daily_tasks"],
            "report_retention_days": plan["report_retention_days"],
            "price_monthly": plan["price_monthly"],
            "price_yearly": plan["price_yearly"],
            "currency": plan["currency"],
            "now": datetime.now(timezone.utc),
        },
    )


def _move_subscriptions_from_legacy_plan(connection, *, legacy_code: str, target_code: str) -> None:
    legacy_plan = _get_plan_by_code(connection, legacy_code)

    if legacy_plan is None:
        return

    target_plan = _get_plan_by_code(connection, target_code)

    if target_plan is None:
        raise RuntimeError(f"Hedef plan bulunamadı: {target_code}")

    connection.execute(
        sa.text(
            """
            UPDATE business_subscriptions
            SET
                plan_id = :target_plan_id,
                max_users_snapshot = :max_users,
                max_managers_snapshot = :max_managers,
                max_daily_tasks_snapshot = :max_daily_tasks,
                report_retention_days_snapshot = :report_retention_days,
                price_monthly_snapshot = :price_monthly,
                price_yearly_snapshot = :price_yearly,
                currency_snapshot = :currency,
                updated_at_utc = :now
            WHERE plan_id = :legacy_plan_id
            """
        ),
        {
            "legacy_plan_id": legacy_plan["id"],
            "target_plan_id": target_plan["id"],
            "max_users": target_plan["max_users"],
            "max_managers": target_plan["max_managers"],
            "max_daily_tasks": target_plan["max_daily_tasks"],
            "report_retention_days": target_plan["report_retention_days"],
            "price_monthly": target_plan["price_monthly"],
            "price_yearly": target_plan["price_yearly"],
            "currency": target_plan["currency"],
            "now": datetime.now(timezone.utc),
        },
    )


def _move_unknown_noncanonical_subscriptions_to_professional(connection) -> None:
    professional_plan = _get_plan_by_code(connection, "professional")

    if professional_plan is None:
        raise RuntimeError("Hedef plan bulunamadı: professional")

    noncanonical_rows = (
        connection.execute(
            sa.text(
                """
                SELECT id, code
                FROM subscription_plans
                WHERE code NOT IN ('trial', 'starter', 'professional', 'enterprise')
                """
            )
        )
        .mappings()
        .all()
    )

    for row in noncanonical_rows:
        connection.execute(
            sa.text(
                """
                UPDATE business_subscriptions
                SET
                    plan_id = :target_plan_id,
                    max_users_snapshot = :max_users,
                    max_managers_snapshot = :max_managers,
                    max_daily_tasks_snapshot = :max_daily_tasks,
                    report_retention_days_snapshot = :report_retention_days,
                    price_monthly_snapshot = :price_monthly,
                    price_yearly_snapshot = :price_yearly,
                    currency_snapshot = :currency,
                    updated_at_utc = :now
                WHERE plan_id = :legacy_plan_id
                """
            ),
            {
                "legacy_plan_id": row["id"],
                "target_plan_id": professional_plan["id"],
                "max_users": professional_plan["max_users"],
                "max_managers": professional_plan["max_managers"],
                "max_daily_tasks": professional_plan["max_daily_tasks"],
                "report_retention_days": professional_plan["report_retention_days"],
                "price_monthly": professional_plan["price_monthly"],
                "price_yearly": professional_plan["price_yearly"],
                "currency": professional_plan["currency"],
                "now": datetime.now(timezone.utc),
            },
        )


def _delete_noncanonical_plans(connection) -> None:
    connection.execute(
        sa.text(
            """
            DELETE FROM subscription_plans
            WHERE code NOT IN ('trial', 'starter', 'professional', 'enterprise')
            """
        )
    )


def upgrade() -> None:
    if not _has_table("subscription_plans"):
        raise RuntimeError("subscription_plans tablosu bulunamadı.")

    if not _has_table("business_subscriptions"):
        raise RuntimeError("business_subscriptions tablosu bulunamadı.")

    connection = op.get_bind()
    now = datetime.now(timezone.utc)

    for plan in CANONICAL_PLANS:
        _upsert_plan(connection, plan, now)

    for plan_code in CANONICAL_PLAN_CODES:
        _sync_subscription_snapshots_for_plan(connection, plan_code)

    for legacy_code, target_code in LEGACY_PLAN_TARGETS.items():
        _move_subscriptions_from_legacy_plan(
            connection,
            legacy_code=legacy_code,
            target_code=target_code,
        )

    _move_unknown_noncanonical_subscriptions_to_professional(connection)
    _delete_noncanonical_plans(connection)


def downgrade() -> None:
    # Bu migration bilinçli olarak sadeleştirici ve veri temizleyici bir migration'dır.
    # Eski plan karmaşasını geri getirmemek için downgrade işlemi veri geri yüklemez.
    pass
