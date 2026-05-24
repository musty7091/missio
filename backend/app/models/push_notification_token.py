from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PushNotificationToken(Base):
    """FCM device token registered for a Missio user."""

    __tablename__ = "push_notification_tokens"
    __table_args__ = (
        Index(
            "ix_push_notification_tokens_user_active",
            "user_id",
            "is_active",
        ),
        Index(
            "ix_push_notification_tokens_business_active",
            "business_id",
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

    fcm_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    device_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    browser_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

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
