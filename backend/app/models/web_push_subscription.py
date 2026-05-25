from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebPushSubscription(Base):
    """Standard Web Push browser subscription registered for a Missio user."""

    __tablename__ = "web_push_subscriptions"
    __table_args__ = (
        Index(
            "ix_web_push_subscriptions_user_active",
            "user_id",
            "is_active",
        ),
        Index(
            "ix_web_push_subscriptions_business_active",
            "business_id",
            "is_active",
        ),
        Index(
            "ix_web_push_subscriptions_endpoint_active",
            "endpoint_hash",
            "is_active",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    business_id: Mapped[int | None] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    endpoint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    endpoint_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    p256dh_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    auth_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_encoding: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="aes128gcm",
    )

    device_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    browser_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    expiration_time_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    last_seen_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
