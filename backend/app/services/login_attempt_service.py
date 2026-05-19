from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt
from app.repositories.user_repository import normalize_username


MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW_MINUTES = 10
LOGIN_LOCKOUT_MINUTES = 10


class LoginAttemptLockedError(ValueError):
    """Raised when login is temporarily blocked."""

    def __init__(self, locked_until_utc: datetime) -> None:
        self.locked_until_utc = locked_until_utc
        super().__init__("Çok fazla hatalı giriş denemesi yapıldı.")


@dataclass(frozen=True)
class FailedLoginAttemptResult:
    """Result returned after recording a failed login attempt."""

    attempt: LoginAttempt
    failed_count: int
    locked_until_utc: datetime | None


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def get_scope_filter(model, business_id: int | None):
    """Return SQLAlchemy business scope filter for nullable business_id."""

    if business_id is None:
        return model.business_id.is_(None)

    return model.business_id == business_id


def normalize_client_text(value: str | None, max_length: int) -> str | None:
    """Normalize optional client supplied text."""

    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    return normalized[:max_length]


def get_latest_success_time(
    db: Session,
    *,
    username: str,
    business_id: int | None,
) -> datetime | None:
    """Return the latest successful login time for the username scope."""

    normalized_username = normalize_username(username)

    statement = (
        select(LoginAttempt.created_at_utc)
        .where(LoginAttempt.username == normalized_username)
        .where(get_scope_filter(LoginAttempt, business_id))
        .where(LoginAttempt.was_successful.is_(True))
        .order_by(desc(LoginAttempt.created_at_utc))
        .limit(1)
    )

    return db.execute(statement).scalar_one_or_none()


def count_recent_failed_attempts(
    db: Session,
    *,
    username: str,
    business_id: int | None,
    now: datetime | None = None,
) -> int:
    """Count recent failed attempts after the latest success."""

    if now is None:
        now = get_utc_now()

    normalized_username = normalize_username(username)
    cutoff = now - timedelta(minutes=LOGIN_ATTEMPT_WINDOW_MINUTES)
    latest_success_time = get_latest_success_time(
        db=db,
        username=normalized_username,
        business_id=business_id,
    )

    statement = (
        select(func.count(LoginAttempt.id))
        .where(LoginAttempt.username == normalized_username)
        .where(get_scope_filter(LoginAttempt, business_id))
        .where(LoginAttempt.was_successful.is_(False))
        .where(LoginAttempt.created_at_utc >= cutoff)
    )

    if latest_success_time is not None:
        statement = statement.where(
            LoginAttempt.created_at_utc > latest_success_time,
        )

    return int(db.execute(statement).scalar_one())


def get_active_lock_until(
    db: Session,
    *,
    username: str,
    business_id: int | None,
    now: datetime | None = None,
) -> datetime | None:
    """Return active lockout end time if there is one."""

    if now is None:
        now = get_utc_now()

    normalized_username = normalize_username(username)

    statement = (
        select(LoginAttempt.locked_until_utc)
        .where(LoginAttempt.username == normalized_username)
        .where(get_scope_filter(LoginAttempt, business_id))
        .where(LoginAttempt.locked_until_utc.is_not(None))
        .where(LoginAttempt.locked_until_utc > now)
        .order_by(desc(LoginAttempt.locked_until_utc))
        .limit(1)
    )

    return db.execute(statement).scalar_one_or_none()


def assert_login_allowed(
    db: Session,
    *,
    username: str,
    business_id: int | None,
    now: datetime | None = None,
) -> None:
    """Raise if login is currently locked for the username scope."""

    locked_until_utc = get_active_lock_until(
        db=db,
        username=username,
        business_id=business_id,
        now=now,
    )

    if locked_until_utc is not None:
        raise LoginAttemptLockedError(locked_until_utc)


def record_failed_login_attempt(
    db: Session,
    *,
    username: str,
    business_id: int | None,
    failure_reason: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> FailedLoginAttemptResult:
    """Record failed login attempt and apply temporary lock if needed."""

    normalized_username = normalize_username(username)
    now = get_utc_now()
    failed_count = (
        count_recent_failed_attempts(
            db=db,
            username=normalized_username,
            business_id=business_id,
            now=now,
        )
        + 1
    )

    locked_until_utc = None

    if failed_count >= MAX_FAILED_LOGIN_ATTEMPTS:
        locked_until_utc = now + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)

    attempt = LoginAttempt(
        business_id=business_id,
        username=normalized_username,
        ip_address=normalize_client_text(ip_address, 100),
        user_agent=normalize_client_text(user_agent, 1000),
        was_successful=False,
        failure_reason=normalize_client_text(failure_reason, 120),
        locked_until_utc=locked_until_utc,
        created_at_utc=now,
    )

    db.add(attempt)
    db.flush()
    db.refresh(attempt)

    return FailedLoginAttemptResult(
        attempt=attempt,
        failed_count=failed_count,
        locked_until_utc=locked_until_utc,
    )


def record_successful_login_attempt(
    db: Session,
    *,
    username: str,
    business_id: int | None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> LoginAttempt:
    """Record successful login attempt."""

    attempt = LoginAttempt(
        business_id=business_id,
        username=normalize_username(username),
        ip_address=normalize_client_text(ip_address, 100),
        user_agent=normalize_client_text(user_agent, 1000),
        was_successful=True,
        failure_reason=None,
        locked_until_utc=None,
        created_at_utc=get_utc_now(),
    )

    db.add(attempt)
    db.flush()
    db.refresh(attempt)

    return attempt
