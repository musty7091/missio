from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BusinessSubscription(Base):
    """Tenant-specific subscription record for a Missio business."""

    __tablename__ = "business_subscriptions"
    __table_args__ = (
        Index(
            "ix_business_subscriptions_business_current",
            "business_id",
            "is_current",
        ),
        Index(
            "ix_business_subscriptions_business_status",
            "business_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("subscription_plans.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="trialing",
        index=True,
    )
    billing_period: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="manual",
    )

    starts_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ends_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    activated_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    suspended_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    max_users_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )
    max_managers_snapshot: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    max_daily_tasks_snapshot: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    report_retention_days_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )

    price_monthly_snapshot: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    price_yearly_snapshot: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    currency_snapshot: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="TRY",
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )