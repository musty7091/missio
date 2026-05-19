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


def create_user(
    db: Session,
    *,
    username: str,
    role: str,
    password: str = "Missio.2026!",
) -> None:
    create_user_with_password(
        db=db,
        full_name=username.title(),
        username=username,
        password=password,
        role=role,
        business_id=None,
        is_active=True,
    )
    db.commit()


def login(client: TestClient, username: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": "Missio.2026!",
        },
    )

    assert response.status_code == 200

    return str(response.json()["access_token"])


def assert_security_headers(response) -> None:
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_security_headers_are_added_to_root(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert_security_headers(response)


def test_me_endpoint_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_endpoint_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Oturum doğrulanamadı."


def test_db_health_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/db/health")

    assert response.status_code == 401


def test_db_health_rejects_staff_user(
    client: TestClient,
    db_session: Session,
) -> None:
    create_user(db_session, username="staffuser", role="staff")
    token = login(client, "staffuser")

    response = client.get(
        "/api/v1/db/health",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_db_health_allows_super_admin(
    client: TestClient,
    db_session: Session,
) -> None:
    create_user(db_session, username="superadmin", role="super_admin")
    token = login(client, "superadmin")

    response = client.get(
        "/api/v1/db/health",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert_security_headers(response)
    assert "password_hash" not in response.text


def test_api_responses_use_no_store_cache_header(
    client: TestClient,
    db_session: Session,
) -> None:
    create_user(db_session, username="superadmin", role="super_admin")
    token = login(client, "superadmin")

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
