from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.tokens import create_access_token
from app.db.base import Base
from app.models.business import Business
from app.models.user import User
from app.services.access_control_service import (
    BusinessScopeError,
    RolePermissionError,
    UserRecordAccessError,
    ensure_business_scope,
    ensure_staff_task_access,
    ensure_user_record_access,
    require_operation_manager_role,
    require_roles,
)
from app.services.auth_service import create_user_with_password
from app.services.session_user_service import (
    AuthenticatedUserMismatchError,
    AuthenticationError,
    get_authenticated_user_from_token,
)


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


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_business(db: Session, slug: str = "test-business") -> Business:
    now = get_utc_now()
    business = Business(
        name="Test Business",
        slug=slug,
        logo_path=None,
        owner_name="Owner",
        phone=None,
        email="owner@example.com",
        address=None,
        timezone="Europe/Istanbul",
        default_theme="dark",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    return business


def create_user(
    db: Session,
    *,
    username: str,
    role: str,
    business_id: int | None,
    is_active: bool = True,
) -> User:
    user = create_user_with_password(
        db=db,
        full_name=username.title(),
        username=username,
        password="Missio.2026!",
        role=role,
        business_id=business_id,
        is_active=is_active,
    )
    db.commit()
    db.refresh(user)

    return user


def test_get_authenticated_user_from_token(db_session: Session) -> None:
    business = create_business(db_session)
    staff = create_user(
        db_session,
        username="staffuser",
        role="staff",
        business_id=business.id,
    )
    token = create_access_token(
        subject=str(staff.id),
        role=staff.role,
        business_id=staff.business_id,
    )

    resolved_user = get_authenticated_user_from_token(db_session, token)

    assert resolved_user.id == staff.id


def test_token_role_mismatch_is_rejected(db_session: Session) -> None:
    business = create_business(db_session)
    staff = create_user(
        db_session,
        username="staffuser",
        role="staff",
        business_id=business.id,
    )
    token = create_access_token(
        subject=str(staff.id),
        role="manager",
        business_id=staff.business_id,
    )

    with pytest.raises(AuthenticatedUserMismatchError):
        get_authenticated_user_from_token(db_session, token)


def test_inactive_user_token_is_rejected(db_session: Session) -> None:
    staff = create_user(
        db_session,
        username="inactiveuser",
        role="staff",
        business_id=None,
        is_active=False,
    )
    token = create_access_token(
        subject=str(staff.id),
        role=staff.role,
        business_id=staff.business_id,
    )

    with pytest.raises(AuthenticationError):
        get_authenticated_user_from_token(db_session, token)


def test_require_roles(db_session: Session) -> None:
    user = create_user(
        db_session,
        username="manageruser",
        role="manager",
        business_id=None,
    )

    require_roles(user, ["manager", "boss"])
    require_operation_manager_role(user)

    with pytest.raises(RolePermissionError):
        require_roles(user, ["staff"])


def test_business_scope_control(db_session: Session) -> None:
    business = create_business(db_session, slug="business-one")
    other_business = create_business(db_session, slug="business-two")
    staff = create_user(
        db_session,
        username="staffuser",
        role="staff",
        business_id=business.id,
    )
    super_admin = create_user(
        db_session,
        username="superadmin",
        role="super_admin",
        business_id=None,
    )

    ensure_business_scope(staff, business.id)
    ensure_business_scope(super_admin, other_business.id)

    with pytest.raises(BusinessScopeError):
        ensure_business_scope(staff, other_business.id)


def test_user_record_access_control(db_session: Session) -> None:
    business = create_business(db_session)
    staff = create_user(
        db_session,
        username="staffuser",
        role="staff",
        business_id=business.id,
    )
    other_staff = create_user(
        db_session,
        username="otherstaff",
        role="staff",
        business_id=business.id,
    )
    boss = create_user(
        db_session,
        username="bossuser",
        role="boss",
        business_id=business.id,
    )

    ensure_user_record_access(staff, staff)
    ensure_user_record_access(boss, staff)

    with pytest.raises(UserRecordAccessError):
        ensure_user_record_access(staff, other_staff)


def test_staff_task_access_control(db_session: Session) -> None:
    business = create_business(db_session)
    staff = create_user(
        db_session,
        username="staffuser",
        role="staff",
        business_id=business.id,
    )
    boss = create_user(
        db_session,
        username="bossuser",
        role="boss",
        business_id=business.id,
    )

    ensure_staff_task_access(
        staff,
        task_business_id=business.id,
        assigned_to_user_id=staff.id,
    )
    ensure_staff_task_access(
        boss,
        task_business_id=business.id,
        assigned_to_user_id=staff.id,
    )

    with pytest.raises(UserRecordAccessError):
        ensure_staff_task_access(
            staff,
            task_business_id=business.id,
            assigned_to_user_id=staff.id + 1,
        )
