from __future__ import annotations

from sqlalchemy import delete
from fastapi.testclient import TestClient

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.login_attempt import LoginAttempt
from app.models.user import User
from app.repositories.user_repository import get_user_by_username, normalize_username
from app.services.auth_service import create_user_with_password


TEST_USERNAME = "missio_auth_endpoint_test"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete test records created by this command."""

    db = SessionLocal()

    try:
        normalized_username = normalize_username(TEST_USERNAME)
        user = get_user_by_username(
            db=db,
            username=normalized_username,
            business_id=None,
        )
        user_id = user.id if user is not None else None

        if user_id is not None:
            db.execute(
                delete(AuditLog).where(AuditLog.user_id == user_id),
            )

        db.execute(
            delete(AuditLog).where(AuditLog.detail.like(f"%{normalized_username}%")),
        )
        db.execute(
            delete(LoginAttempt).where(LoginAttempt.username == normalized_username),
        )
        db.execute(
            delete(User).where(User.username == normalized_username),
        )
        db.commit()
    finally:
        db.close()


def create_test_user() -> None:
    """Create local test user."""

    db = SessionLocal()

    try:
        create_user_with_password(
            db=db,
            full_name="Missio Auth Endpoint Test",
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="missio.auth.endpoint@example.com",
            is_active=True,
        )
        db.commit()
    finally:
        db.close()


def main() -> None:
    """Run auth endpoint smoke checks."""

    cleanup_test_data()
    create_test_user()

    client = TestClient(app)

    try:
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
            },
        )

        if login_response.status_code != 200:
            raise RuntimeError(
                f"Login endpoint beklenen 200 yerine "
                f"{login_response.status_code} döndü: {login_response.text}"
            )

        login_data = login_response.json()
        access_token = login_data.get("access_token")

        if not access_token:
            raise RuntimeError("Login response access_token içermiyor.")

        if login_data.get("token_type") != "bearer":
            raise RuntimeError("Login response token_type bearer değil.")

        if "password_hash" in login_data:
            raise RuntimeError("Login response password_hash sızdırıyor.")

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if me_response.status_code != 200:
            raise RuntimeError(
                f"Me endpoint beklenen 200 yerine "
                f"{me_response.status_code} döndü: {me_response.text}"
            )

        me_data = me_response.json()

        if me_data.get("username") != TEST_USERNAME:
            raise RuntimeError("Me endpoint username bilgisi hatalı.")

        if "password_hash" in me_data:
            raise RuntimeError("Me endpoint password_hash sızdırıyor.")

        wrong_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": TEST_USERNAME,
                "password": "Wrong.2026!",
            },
        )

        if wrong_response.status_code != 401:
            raise RuntimeError("Hatalı şifre güvenli şekilde reddedilmedi.")

        print("Login endpoint başarı kontrolü başarılı.")
        print("Me endpoint token kontrolü başarılı.")
        print("Güvenli hata cevabı kontrolü başarılı.")
        print("Auth endpoint temel kontrolü başarılı.")
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    main()
