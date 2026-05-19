from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business import Business


def get_business_by_slug(db: Session, slug: str) -> Business | None:
    """Return business by normalized slug."""

    normalized_slug = slug.strip().lower()
    statement = select(Business).where(Business.slug == normalized_slug)

    return db.execute(statement).scalar_one_or_none()


def is_business_slug_taken(db: Session, slug: str) -> bool:
    """Return whether a business slug already exists."""

    return get_business_by_slug(db=db, slug=slug) is not None


def add_business(db: Session, business: Business) -> Business:
    """Add business to session and flush it."""

    db.add(business)
    db.flush()
    db.refresh(business)

    return business
