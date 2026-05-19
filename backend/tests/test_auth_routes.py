from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.login_attempt import LoginAttempt
from app.services.auth_service import create_user_with_password


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


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def create_test_user(
    db: Session,
    *,
    username: str = "loginuser",
    password: str = "Missio.2026!",
    is_active: bool = True,
) -> None:
    create_user_with_password(
        db=db,
        full_name="Login User",
        username=username,
        password=password,
        role="super_admin",
        business_id=None,
        email="login@example.com",
        is_active=is_active,
    )
    db.commit()


def test_login_endpoint_returns_access_token(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_user(db_session)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "loginuser",
            "password": "Missio.2026!",
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in_minutes"] > 0
    assert "password_hash" not in data


def test_me_endpoint_returns_safe_current_user(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_user(db_session)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "loginuser",
            "password": "Missio.2026!",
        },
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.json()

    assert response.status_code == 200
    assert data["username"] == "loginuser"
    assert data["role"] == "super_admin"
    assert "password_hash" not in data


def test_login_endpoint_rejects_wrong_password(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_user(db_session)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "loginuser",
            "password": "Wrong.2026!",
        },
    )

    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Kullanıcı adı veya şifre hatalı."
    assert "access_token" not in data


def test_login_endpoint_rejects_inactive_user_with_generic_message(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_user(db_session, username="inactiveuser", is_active=False)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "inactiveuser",
            "password": "Missio.2026!",
        },
    )

    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Kullanıcı adı veya şifre hatalı."


def test_login_endpoint_applies_bruteforce_lock(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_user(db_session)

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "Wrong.2026!",
            },
        )
        assert response.status_code == 401

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "loginuser",
            "password": "Missio.2026!",
        },
    )

    attempts = db_session.query(LoginAttempt).all()

    assert response.status_code == 429
    assert attempts
