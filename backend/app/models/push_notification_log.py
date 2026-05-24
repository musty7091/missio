from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PushNotificationLog(Base):
    """Push notification delivery log."""

    __tablename__ = "push_notification_logs"
    __table_args__ = (
        Index(
            "ix_push_notification_logs_business_type",
            "business_id",
            "notification_type",
        ),
        Index(
            "ix_push_notification_logs_user_status",
            "user_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    business_id: Mapped[int | None] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    token_id: Mapped[int | None] = mapped_column(
        ForeignKey("push_notification_tokens.id"),
        nullable=True,
        index=True,
    )

    notification_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    data_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fcm_message_id: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    sent_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
