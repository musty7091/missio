from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.tokens import decode_access_token
from app.db.base import Base
from app.models.business import Business
from app.services.auth_service import (
    DuplicateUsernameError,
    InactiveUserError,
    InvalidCredentialsError,
    WeakPasswordError,
    authenticate_user,
    create_login_token_for_user,
    create_user_with_password,
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


def create_business(db: Session) -> Business:
    business = Business(
        name="Test İşletme",
        slug="test-isletme",
        logo_path=None,
        owner_name="Test Owner",
        phone=None,
        email="owner@example.com",
        address=None,
        timezone="Europe/Istanbul",
        default_theme="dark",
        is_active=True,
        created_at=create_user_with_password.__globals__["get_utc_now"](),
        updated_at=create_user_with_password.__globals__["get_utc_now"](),
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    return business


def test_create_user_with_password_hashes_password(db_session: Session) -> None:
    user = create_user_with_password(
        db=db_session,
        full_name="Test User",
        username="TestUser",
        password="Missio.2026!",
        role="super_admin",
        business_id=None,
        email="TEST@EXAMPLE.COM",
    )

    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert "Missio.2026!" not in user.password_hash


def test_create_user_rejects_weak_password(db_session: Session) -> None:
    with pytest.raises(WeakPasswordError):
        create_user_with_password(
            db=db_session,
            full_name="Weak User",
            username="weakuser",
            password="123",
            role="staff",
            business_id=None,
        )


def test_create_user_rejects_duplicate_username(db_session: Session) -> None:
    create_user_with_password(
        db=db_session,
        full_name="First User",
        username="sameuser",
        password="Missio.2026!",
        role="super_admin",
        business_id=None,
    )
    db_session.commit()

    with pytest.raises(DuplicateUsernameError):
        create_user_with_password(
            db=db_session,
            full_name="Second User",
            username="sameuser",
            password="Missio.2026!",
            role="super_admin",
            business_id=None,
        )


def test_authenticate_user_updates_last_login(db_session: Session) -> None:
    user = create_user_with_password(
        db=db_session,
        full_name="Login User",
        username="loginuser",
        password="Missio.2026!",
        role="super_admin",
        business_id=None,
    )
    db_session.commit()
    db_session.refresh(user)

    authenticated_user = authenticate_user(
        db=db_session,
        username="loginuser",
        password="Missio.2026!",
        business_id=None,
    )

    assert authenticated_user.id == user.id
    assert authenticated_user.last_login_at is not None


def test_authenticate_user_rejects_wrong_password(db_session: Session) -> None:
    create_user_with_password(
        db=db_session,
        full_name="Wrong Password User",
        username="wrongpassword",
        password="Missio.2026!",
        role="super_admin",
        business_id=None,
    )
    db_session.commit()

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            db=db_session,
            username="wrongpassword",
            password="Wrong.2026!",
            business_id=None,
        )


def test_authenticate_user_rejects_inactive_user(db_session: Session) -> None:
    create_user_with_password(
        db=db_session,
        full_name="Inactive User",
        username="inactiveuser",
        password="Missio.2026!",
        role="super_admin",
        business_id=None,
        is_active=False,
    )
    db_session.commit()

    with pytest.raises(InactiveUserError):
        authenticate_user(
            db=db_session,
            username="inactiveuser",
            password="Missio.2026!",
            business_id=None,
        )


def test_create_login_token_for_business_user(db_session: Session) -> None:
    business = create_business(db_session)

    user = create_user_with_password(
        db=db_session,
        full_name="Staff User",
        username="staffuser",
        password="Missio.2026!",
        role="staff",
        business_id=business.id,
    )
    db_session.commit()
    db_session.refresh(user)

    login_token = create_login_token_for_user(user)
    payload = decode_access_token(login_token.access_token)

    assert login_token.token_type == "bearer"
    assert payload.subject == str(user.id)
    assert payload.role == "staff"
    assert payload.business_id == business.id
