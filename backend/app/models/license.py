from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class License(Base):
    """License and package record for a business."""

    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    package_code: Mapped[str] = mapped_column(
        ForeignKey("packages.code"),
        nullable=False,
        index=True,
    )
    license_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    license_owner: Mapped[str | None] = mapped_column(String(200), nullable=True)
    starts_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_lifetime: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
