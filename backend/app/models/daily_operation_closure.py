from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyOperationClosure(Base):
    """Official end-of-day operation closure snapshot."""

    __tablename__ = "daily_operation_closures"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "closure_date",
            name="uq_daily_operation_closures_business_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    closure_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    closed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    closed_by_user_full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    closed_by_username: Mapped[str] = mapped_column(String(100), nullable=False)
    closed_by_role: Mapped[str] = mapped_column(String(50), nullable=False)
    closed_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="closed", index=True)
    manager_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_by_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    total_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approval_pending_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    photo_required_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    photo_evidence_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
