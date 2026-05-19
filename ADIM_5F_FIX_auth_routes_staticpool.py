from __future__ import annotations

from pathlib import Path
import py_compile

ROOT_DIR = Path(r"C:\missio")

FILES = {'backend/tests/test_auth_routes.py': 'from collections.abc import Generator\n\nimport pytest\nfrom fastapi.testclient import TestClient\nfrom sqlalchemy import create_engine, event\nfrom sqlalchemy.orm import Session, sessionmaker\nfrom sqlalchemy.pool import StaticPool\n\nimport app.models  # noqa: F401\nfrom app.db.base import Base\nfrom app.db.session import get_db\nfrom app.main import app\nfrom app.models.login_attempt import LoginAttempt\nfrom app.services.auth_service import create_user_with_password\n\n\n@pytest.fixture()\ndef db_session() -> Generator[Session, None, None]:\n    engine = create_engine(\n        "sqlite://",\n        connect_args={"check_same_thread": False},\n        poolclass=StaticPool,\n    )\n\n    @event.listens_for(engine, "connect")\n    def enable_foreign_keys(dbapi_connection, connection_record) -> None:\n        del connection_record\n        cursor = dbapi_connection.cursor()\n        cursor.execute("PRAGMA foreign_keys=ON")\n        cursor.close()\n\n    TestingSessionLocal = sessionmaker(\n        autocommit=False,\n        autoflush=False,\n        bind=engine,\n    )\n\n    Base.metadata.create_all(bind=engine)\n\n    db = TestingSessionLocal()\n\n    try:\n        yield db\n    finally:\n        db.close()\n        Base.metadata.drop_all(bind=engine)\n        engine.dispose()\n\n\n@pytest.fixture()\ndef client(db_session: Session) -> Generator[TestClient, None, None]:\n    def override_get_db() -> Generator[Session, None, None]:\n        yield db_session\n\n    app.dependency_overrides[get_db] = override_get_db\n\n    try:\n        with TestClient(app) as test_client:\n            yield test_client\n    finally:\n        app.dependency_overrides.clear()\n\n\ndef create_test_user(\n    db: Session,\n    *,\n    username: str = "loginuser",\n    password: str = "Missio.2026!",\n    is_active: bool = True,\n) -> None:\n    create_user_with_password(\n        db=db,\n        full_name="Login User",\n        username=username,\n        password=password,\n        role="super_admin",\n        business_id=None,\n        email="login@example.com",\n        is_active=is_active,\n    )\n    db.commit()\n\n\ndef test_login_endpoint_returns_access_token(\n    client: TestClient,\n    db_session: Session,\n) -> None:\n    create_test_user(db_session)\n\n    response = client.post(\n        "/api/v1/auth/login",\n        json={\n            "username": "loginuser",\n            "password": "Missio.2026!",\n        },\n    )\n\n    data = response.json()\n\n    assert response.status_code == 200\n    assert data["access_token"]\n    assert data["token_type"] == "bearer"\n    assert data["expires_in_minutes"] > 0\n    assert "password_hash" not in data\n\n\ndef test_me_endpoint_returns_safe_current_user(\n    client: TestClient,\n    db_session: Session,\n) -> None:\n    create_test_user(db_session)\n\n    login_response = client.post(\n        "/api/v1/auth/login",\n        json={\n            "username": "loginuser",\n            "password": "Missio.2026!",\n        },\n    )\n    access_token = login_response.json()["access_token"]\n\n    response = client.get(\n        "/api/v1/auth/me",\n        headers={"Authorization": f"Bearer {access_token}"},\n    )\n\n    data = response.json()\n\n    assert response.status_code == 200\n    assert data["username"] == "loginuser"\n    assert data["role"] == "super_admin"\n    assert "password_hash" not in data\n\n\ndef test_login_endpoint_rejects_wrong_password(\n    client: TestClient,\n    db_session: Session,\n) -> None:\n    create_test_user(db_session)\n\n    response = client.post(\n        "/api/v1/auth/login",\n        json={\n            "username": "loginuser",\n            "password": "Wrong.2026!",\n        },\n    )\n\n    data = response.json()\n\n    assert response.status_code == 401\n    assert data["detail"] == "Kullanıcı adı veya şifre hatalı."\n    assert "access_token" not in data\n\n\ndef test_login_endpoint_rejects_inactive_user_with_generic_message(\n    client: TestClient,\n    db_session: Session,\n) -> None:\n    create_test_user(db_session, username="inactiveuser", is_active=False)\n\n    response = client.post(\n        "/api/v1/auth/login",\n        json={\n            "username": "inactiveuser",\n            "password": "Missio.2026!",\n        },\n    )\n\n    data = response.json()\n\n    assert response.status_code == 401\n    assert data["detail"] == "Kullanıcı adı veya şifre hatalı."\n\n\ndef test_login_endpoint_applies_bruteforce_lock(\n    client: TestClient,\n    db_session: Session,\n) -> None:\n    create_test_user(db_session)\n\n    for _ in range(5):\n        response = client.post(\n            "/api/v1/auth/login",\n            json={\n                "username": "loginuser",\n                "password": "Wrong.2026!",\n            },\n        )\n        assert response.status_code == 401\n\n    response = client.post(\n        "/api/v1/auth/login",\n        json={\n            "username": "loginuser",\n            "password": "Missio.2026!",\n        },\n    )\n\n    attempts = db_session.query(LoginAttempt).all()\n\n    assert response.status_code == 429\n    assert attempts\n'}


def write_file(relative_path: str, content: str) -> None:
    target = ROOT_DIR / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"Yazildi: {target}")


def compile_files() -> None:
    for relative_path in FILES:
        if relative_path.endswith(".py"):
            py_compile.compile(str(ROOT_DIR / relative_path), doraise=True)

    print("Python syntax kontrolu basarili.")


def main() -> None:
    print("Missio ADIM 5F test veritabani duzeltmesi basladi.")
    print("")

    for relative_path, content in FILES.items():
        write_file(relative_path, content)

    compile_files()

    print("")
    print("Tamamlandi.")
    print("Not: FastAPI TestClient farkli thread kullandigi icin auth route testlerinde")
    print("SQLite in-memory veritabani StaticPool ile paylastirildi.")


if __name__ == "__main__":
    main()
