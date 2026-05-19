from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.models.audit_log import AuditLog
from app.models.login_attempt import LoginAttempt
from app.repositories.user_repository import normalize_username
from app.services.auth_service import (
    AccountTemporarilyLockedError,
    InvalidCredentialsError,
    authenticate_user,
    create_user_with_password,
)
from app.services.login_attempt_service import count_recent_failed_attempts


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_test_user(db: Session, username: str = "loginuser") -> None:
    create_user_with_password(
        db=db,
        full_name="Login User",
        username=username,
        password="Missio.2026!",
        role="super_admin",
        business_id=None,
    )
    db.commit()


def test_failed_login_records_attempt_and_audit_log(db_session: Session) -> None:
    create_test_user(db_session)

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            db=db_session,
            username="loginuser",
            password="Wrong.2026!",
            business_id=None,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    attempts = db_session.execute(select(LoginAttempt)).scalars().all()
    audit_logs = db_session.execute(select(AuditLog)).scalars().all()

    assert len(attempts) == 1
    assert attempts[0].username == "loginuser"
    assert attempts[0].was_successful is False
    assert attempts[0].failure_reason == "invalid_credentials"
    assert len(audit_logs) == 1
    assert audit_logs[0].action == "auth.login_failed"
    assert "Wrong.2026!" not in (audit_logs[0].detail or "")


def test_bruteforce_lock_after_five_failed_attempts(db_session: Session) -> None:
    create_test_user(db_session)

    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(
                db=db_session,
                username="loginuser",
                password="Wrong.2026!",
                business_id=None,
            )

    with pytest.raises(AccountTemporarilyLockedError):
        authenticate_user(
            db=db_session,
            username="loginuser",
            password="Missio.2026!",
            business_id=None,
        )

    attempts = db_session.execute(select(LoginAttempt)).scalars().all()
    locked_attempts = [
        attempt
        for attempt in attempts
        if attempt.locked_until_utc is not None
    ]

    assert len(attempts) == 5
    assert locked_attempts


def test_successful_login_records_attempt_and_audit_log(db_session: Session) -> None:
    create_test_user(db_session)

    user = authenticate_user(
        db=db_session,
        username="loginuser",
        password="Missio.2026!",
        business_id=None,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    attempts = db_session.execute(select(LoginAttempt)).scalars().all()
    audit_logs = db_session.execute(select(AuditLog)).scalars().all()

    assert user.last_login_at is not None
    assert len(attempts) == 1
    assert attempts[0].was_successful is True
    assert len(audit_logs) == 1
    assert audit_logs[0].action == "auth.login_success"


def test_successful_login_resets_recent_failed_count(db_session: Session) -> None:
    create_test_user(db_session)

    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(
                db=db_session,
                username="loginuser",
                password="Wrong.2026!",
                business_id=None,
            )

    authenticate_user(
        db=db_session,
        username="loginuser",
        password="Missio.2026!",
        business_id=None,
    )

    failed_count = count_recent_failed_attempts(
        db=db_session,
        username="loginuser",
        business_id=None,
    )

    assert failed_count == 0


def test_unknown_user_login_records_failed_attempt(db_session: Session) -> None:
    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            db=db_session,
            username="ghostuser",
            password="Missio.2026!",
            business_id=None,
        )

    attempts = db_session.execute(select(LoginAttempt)).scalars().all()

    assert len(attempts) == 1
    assert attempts[0].username == normalize_username("ghostuser")
    assert attempts[0].was_successful is False
