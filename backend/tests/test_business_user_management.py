from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.roles import UserRole
from app.db.base import Base
from app.models.audit_log import AuditLog
from app.models.business import Business
from app.models.user import User
from app.services.access_control_service import RolePermissionError
from app.services.auth_service import (
    DuplicateUsernameError,
    WeakPasswordError,
    create_user_with_password,
)
from app.services.business_service import create_business_with_owner
from app.services.user_management_service import (
    InvalidBusinessUserRoleError,
    create_business_user,
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


def create_super_admin(db: Session) -> User:
    user = create_user_with_password(
        db=db,
        full_name="Super Admin",
        username="superadmin",
        password="Missio.2026!",
        role=UserRole.SUPER_ADMIN.value,
        business_id=None,
    )
    db.commit()
    db.refresh(user)

    return user


def create_staff_without_business(db: Session) -> User:
    user = create_user_with_password(
        db=db,
        full_name="Staff User",
        username="staffuser",
        password="Missio.2026!",
        role=UserRole.STAFF.value,
        business_id=None,
    )
    db.commit()
    db.refresh(user)

    return user


def create_business_fixture(db: Session, super_admin: User) -> Business:
    result = create_business_with_owner(
        db=db,
        current_user=super_admin,
        business_name="Test Business",
        business_slug="test-business",
        owner_full_name="Boss User",
        owner_username="bossuser",
        owner_password="Missio.2026!",
    )
    db.commit()
    db.refresh(result.business)

    return result.business


def test_create_manager_user(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)
    business = create_business_fixture(db_session, super_admin)

    user = create_business_user(
        db=db_session,
        current_user=super_admin,
        business=business,
        full_name="Manager User",
        username="manageruser",
        password="Missio.2026!",
        role="manager",
        email="manager@example.com",
    )
    db_session.commit()
    db_session.refresh(user)

    audit_logs = db_session.execute(select(AuditLog)).scalars().all()
    actions = {audit_log.action for audit_log in audit_logs}

    assert user.business_id == business.id
    assert user.role == "manager"
    assert user.email == "manager@example.com"
    assert "business.user_created" in actions
    assert all("Missio.2026!" not in (audit_log.detail or "") for audit_log in audit_logs)


def test_create_staff_user(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)
    business = create_business_fixture(db_session, super_admin)

    user = create_business_user(
        db=db_session,
        current_user=super_admin,
        business=business,
        full_name="Staff User",
        username="staffmember",
        password="Missio.2026!",
        role="staff",
    )
    db_session.commit()
    db_session.refresh(user)

    assert user.business_id == business.id
    assert user.role == "staff"


def test_create_business_user_requires_super_admin(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)
    business = create_business_fixture(db_session, super_admin)
    staff = create_staff_without_business(db_session)

    with pytest.raises(RolePermissionError):
        create_business_user(
            db=db_session,
            current_user=staff,
            business=business,
            full_name="Forbidden User",
            username="forbiddenuser",
            password="Missio.2026!",
            role="staff",
        )


def test_create_business_user_rejects_super_admin_role(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)
    business = create_business_fixture(db_session, super_admin)

    with pytest.raises(InvalidBusinessUserRoleError):
        create_business_user(
            db=db_session,
            current_user=super_admin,
            business=business,
            full_name="Wrong Role User",
            username="wrongroleuser",
            password="Missio.2026!",
            role="super_admin",
        )


def test_create_business_user_rejects_weak_password(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)
    business = create_business_fixture(db_session, super_admin)

    with pytest.raises(WeakPasswordError):
        create_business_user(
            db=db_session,
            current_user=super_admin,
            business=business,
            full_name="Weak Password User",
            username="weakpassworduser",
            password="123",
            role="staff",
        )


def test_create_business_user_rejects_duplicate_username_in_same_business(
    db_session: Session,
) -> None:
    super_admin = create_super_admin(db_session)
    business = create_business_fixture(db_session, super_admin)

    create_business_user(
        db=db_session,
        current_user=super_admin,
        business=business,
        full_name="First Staff",
        username="samestaff",
        password="Missio.2026!",
        role="staff",
    )
    db_session.commit()

    with pytest.raises(DuplicateUsernameError):
        create_business_user(
            db=db_session,
            current_user=super_admin,
            business=business,
            full_name="Second Staff",
            username="samestaff",
            password="Missio.2026!",
            role="staff",
        )
