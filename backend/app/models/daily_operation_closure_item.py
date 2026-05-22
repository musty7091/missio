from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyOperationClosureItem(Base):
    """Task row snapshot inside an end-of-day operation closure."""

    __tablename__ = "daily_operation_closure_items"
    __table_args__ = (
        UniqueConstraint(
            "closure_id",
            "task_id",
            name="uq_daily_operation_closure_items_closure_task",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    closure_id: Mapped[int] = mapped_column(
        ForeignKey("daily_operation_closures.id"),
        nullable=False,
        index=True,
    )
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    task_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    assigned_to_user_full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    assigned_to_username: Mapped[str | None] = mapped_column(String(100), nullable=True)

    task_title: Mapped[str] = mapped_column(String(200), nullable=False)
    task_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(30), nullable=False)
    task_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    task_priority: Mapped[str] = mapped_column(String(30), nullable=False)

    requires_photo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_manager_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_photo_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    assigned_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
