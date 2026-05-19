from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.models.app_setting import AppSetting
from app.models.audit_log import AuditLog
from app.services.auth_service import WeakPasswordError
from app.services.bootstrap_service import (
    BootstrapAlreadyCompletedError,
    BootstrapInconsistentStateError,
    create_initial_super_admin,
    get_bootstrap_status,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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


def test_bootstrap_status_ready_when_no_users(db_session: Session) -> None:
    status = get_bootstrap_status(db_session)

    assert status.user_count == 0
    assert status.super_admin_count == 0
    assert status.setup_completed is False
    assert status.is_ready_for_initial_setup is True
    assert status.is_consistent is True


def test_create_initial_super_admin(db_session: Session) -> None:
    user = create_initial_super_admin(
        db=db_session,
        full_name="Mustafa Karadeniz",
        username="mustafa",
        password="Missio.2026!",
        email="mustafa@example.com",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    db_session.commit()
    db_session.refresh(user)

    status = get_bootstrap_status(db_session)
    audit_logs = db_session.execute(select(AuditLog)).scalars().all()

    assert user.id is not None
    assert user.business_id is None
    assert user.role == "super_admin"
    assert user.is_active is True
    assert status.is_completed is True
    assert status.setup_completed is True
    assert status.super_admin_count == 1
    assert len(audit_logs) == 1
    assert audit_logs[0].action == "setup.super_admin_created"
    assert "Missio.2026!" not in (audit_logs[0].detail or "")


def test_bootstrap_rejects_second_super_admin_creation(db_session: Session) -> None:
    create_initial_super_admin(
        db=db_session,
        full_name="First Admin",
        username="firstadmin",
        password="Missio.2026!",
    )
    db_session.commit()

    with pytest.raises(BootstrapAlreadyCompletedError):
        create_initial_super_admin(
            db=db_session,
            full_name="Second Admin",
            username="secondadmin",
            password="Missio.2026!",
        )


def test_bootstrap_rejects_weak_password(db_session: Session) -> None:
    with pytest.raises(WeakPasswordError):
        create_initial_super_admin(
            db=db_session,
            full_name="Weak Admin",
            username="weakadmin",
            password="123",
        )


def test_bootstrap_detects_inconsistent_setup_completed_without_user(
    db_session: Session,
) -> None:
    app_settings = AppSetting(
        app_name="Missio",
        default_timezone="Europe/Istanbul",
        default_theme="dark",
        setup_completed=True,
        created_at=create_initial_super_admin.__globals__["get_utc_now"](),
        updated_at=create_initial_super_admin.__globals__["get_utc_now"](),
    )
    db_session.add(app_settings)
    db_session.commit()

    status = get_bootstrap_status(db_session)

    assert status.is_consistent is False

    with pytest.raises(BootstrapInconsistentStateError):
        create_initial_super_admin(
            db=db_session,
            full_name="Admin",
            username="admin",
            password="Missio.2026!",
        )
