from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskTemplate(Base):
    """Reusable daily routine task template assigned to manager or staff."""

    __tablename__ = "task_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    assigned_to_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_categories.id"),
        nullable=True,
        index=True,
    )
    recurrence_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="daily",
        index=True,
    )
    default_priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="normal",
    )
    default_due_time_local: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )
    default_due_offset_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_photo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_manager_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)