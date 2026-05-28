from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LocationCheck(Base):
    """Manual location check request created by boss or manager for a staff member."""

    __tablename__ = "location_checks"
    __table_args__ = (
        Index(
            "ix_location_checks_business_status",
            "business_id",
            "status",
        ),
        Index(
            "ix_location_checks_target_status",
            "target_user_id",
            "status",
        ),
        Index(
            "ix_location_checks_request_group",
            "request_group_id",
        ),
        Index(
            "ix_location_checks_requested_at",
            "requested_at_utc",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    request_group_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    requested_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    target_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="pending",
        index=True,
    )

    request_note: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    staff_seen_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    responded_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    location_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)

    response_error_code: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    response_error_message: Mapped[str | None] = mapped_column(
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

    requested_at_utc: Mapped[datetime] = mapped_column(
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
