from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def normalize_username(username: str) -> str:
    """Normalize usernames before storing or querying."""

    return username.strip().lower()


def normalize_email(email: str | None) -> str | None:
    """Normalize email address before storing or querying."""

    if email is None:
        return None

    normalized = email.strip().lower()

    if not normalized:
        return None

    return normalized


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Return user by primary key."""

    statement = select(User).where(User.id == user_id)

    return db.execute(statement).scalar_one_or_none()


def get_user_by_username(
    db: Session,
    username: str,
    business_id: int | None = None,
) -> User | None:
    """Return user by normalized username and business scope."""

    normalized_username = normalize_username(username)

    statement = select(User).where(User.username == normalized_username)

    if business_id is None:
        statement = statement.where(User.business_id.is_(None))
    else:
        statement = statement.where(User.business_id == business_id)

    return db.execute(statement).scalar_one_or_none()


def is_username_taken(
    db: Session,
    username: str,
    business_id: int | None = None,
) -> bool:
    """Return whether the username already exists in the business scope."""

    return get_user_by_username(
        db=db,
        username=username,
        business_id=business_id,
    ) is not None


def add_user(db: Session, user: User) -> User:
    """Add user to session and flush it."""

    db.add(user)
    db.flush()
    db.refresh(user)

    return user


def update_last_login_at(db: Session, user: User) -> User:
    """Flush last_login_at changes for a user."""

    db.add(user)
    db.flush()
    db.refresh(user)

    return user
