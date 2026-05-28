from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PasswordResetRequest(Base):
    """Password reset request created from the public forgot-password flow."""

    __tablename__ = "password_reset_requests"
    __table_args__ = (
        Index(
            "ix_password_reset_requests_business_status",
            "business_id",
            "status",
        ),
        Index(
            "ix_password_reset_requests_target_status",
            "target_user_id",
            "status",
        ),
        Index(
            "ix_password_reset_requests_requested_at",
            "requested_at_utc",
        ),
        Index(
            "ix_password_reset_requests_resolved_by",
            "resolved_by_user_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    target_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    requested_username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="pending",
        index=True,
    )

    notification_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="not_attempted",
        index=True,
    )

    notification_attempted_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    notification_sent_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    notification_failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_notification_attempt_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    requested_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    resolved_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    resolution_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )