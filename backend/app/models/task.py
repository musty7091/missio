from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base


class Task(Base):
    """Main operational task assigned to manager or staff."""

    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "template_id",
            "assigned_to_user_id",
            "task_date",
            name="uq_tasks_business_template_user_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_templates.id"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_categories.id"),
        nullable=True,
        index=True,
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    task_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="extra",
        index=True,
    )
    task_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(String(30), nullable=False, default="normal")
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="assigned",
        index=True,
    )
    due_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_arrived_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requires_photo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_manager_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @validates("requires_photo", "requires_location", "requires_manager_approval")
    def validate_manager_approval_requirement(self, key: str, value: object) -> bool:
        """Force manager approval when task needs photo proof or location proof."""

        normalized_value = bool(value)

        if key == "requires_manager_approval":
            if bool(self.requires_photo) or bool(self.requires_location):
                return True

            return normalized_value

        if key == "requires_photo":
            if normalized_value or bool(self.requires_location):
                self.requires_manager_approval = True

            return normalized_value

        if key == "requires_location":
            if normalized_value or bool(self.requires_photo):
                self.requires_manager_approval = True

            return normalized_value

        return normalized_value
