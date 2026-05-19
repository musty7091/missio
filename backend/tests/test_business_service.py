from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.roles import UserRole
from app.db.base import Base
from app.models.audit_log import AuditLog
from app.services.access_control_service import RolePermissionError
from app.services.auth_service import WeakPasswordError, create_user_with_password
from app.services.business_service import (
    DuplicateBusinessSlugError,
    InvalidBusinessOwnerRoleError,
    create_business_with_owner,
    normalize_business_slug,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_super_admin(db: Session):
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


def create_staff(db: Session):
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


def test_normalize_business_slug() -> None:
    assert normalize_business_slug("Ertan Market") == "ertan-market"
    assert normalize_business_slug("Şişli Çözüm İşleri") == "sisli-cozum-isleri"


def test_create_business_with_owner(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)
    result = create_business_with_owner(
        db=db_session,
        current_user=super_admin,
        business_name="Ertan Market",
        business_slug="Ertan Market",
        owner_full_name="Ertan Patron",
        owner_username="ertanpatron",
        owner_password="Missio.2026!",
        owner_email="ertan@example.com",
        business_phone="0533 000 00 00",
    )
    db_session.commit()
    db_session.refresh(result.business)
    db_session.refresh(result.owner_user)

    audit_logs = db_session.execute(select(AuditLog)).scalars().all()
    actions = {audit_log.action for audit_log in audit_logs}

    assert result.business.id is not None
    assert result.business.slug == "ertan-market"
    assert result.owner_user.business_id == result.business.id
    assert result.owner_user.role == "boss"
    assert "business.created" in actions
    assert "business.owner_created" in actions
    assert all("Missio.2026!" not in (audit_log.detail or "") for audit_log in audit_logs)


def test_create_business_rejects_duplicate_slug(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)
    create_business_with_owner(
        db=db_session,
        current_user=super_admin,
        business_name="First Business",
        business_slug="same-business",
        owner_full_name="First Owner",
        owner_username="firstowner",
        owner_password="Missio.2026!",
    )
    db_session.commit()

    with pytest.raises(DuplicateBusinessSlugError):
        create_business_with_owner(
            db=db_session,
            current_user=super_admin,
            business_name="Second Business",
            business_slug="same-business",
            owner_full_name="Second Owner",
            owner_username="secondowner",
            owner_password="Missio.2026!",
        )


def test_create_business_requires_super_admin(db_session: Session) -> None:
    staff = create_staff(db_session)

    with pytest.raises(RolePermissionError):
        create_business_with_owner(
            db=db_session,
            current_user=staff,
            business_name="Forbidden Business",
            business_slug="forbidden-business",
            owner_full_name="Forbidden Owner",
            owner_username="forbiddenowner",
            owner_password="Missio.2026!",
        )


def test_create_business_owner_rejects_weak_password(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)

    with pytest.raises(WeakPasswordError):
        create_business_with_owner(
            db=db_session,
            current_user=super_admin,
            business_name="Weak Business",
            business_slug="weak-business",
            owner_full_name="Weak Owner",
            owner_username="weakowner",
            owner_password="123",
        )


def test_create_business_owner_rejects_invalid_owner_role(db_session: Session) -> None:
    super_admin = create_super_admin(db_session)

    with pytest.raises(InvalidBusinessOwnerRoleError):
        create_business_with_owner(
            db=db_session,
            current_user=super_admin,
            business_name="Invalid Role Business",
            business_slug="invalid-role-business",
            owner_full_name="Invalid Role Owner",
            owner_username="invalidroleowner",
            owner_password="Missio.2026!",
            owner_role="staff",
        )
