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


SUPER_ADMIN_USERNAME = "missio_api_security_admin"
STAFF_USERNAME = "missio_api_security_staff"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete records created by this command."""

    db = SessionLocal()

    try:
        for username in [SUPER_ADMIN_USERNAME, STAFF_USERNAME]:
            normalized_username = normalize_username(username)
            user = get_user_by_username(
                db=db,
                username=normalized_username,
                business_id=None,
            )

            if user is not None:
                db.delete(user)

            db.execute(
                delete(LoginAttempt).where(
                    LoginAttempt.username == normalized_username,
                ),
            )
            db.execute(
                delete(AuditLog).where(
                    AuditLog.detail.like(f"%{normalized_username}%"),
                ),
            )

        db.commit()
    finally:
        db.close()


def create_test_users() -> None:
    """Create local users for API security checks."""

    db = SessionLocal()

    try:
        create_user_with_password(
            db=db,
            full_name="Missio API Security Admin",
            username=SUPER_ADMIN_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="missio.api.security.admin@example.com",
            is_active=True,
        )
        create_user_with_password(
            db=db,
            full_name="Missio API Security Staff",
            username=STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            business_id=None,
            email="missio.api.security.staff@example.com",
            is_active=True,
        )
        db.commit()
    finally:
        db.close()


def login_and_get_token(client: TestClient, username: str) -> str:
    """Login and return access token."""

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": TEST_PASSWORD,
        },
    )

    if response.status_code != 200:
        raise RuntimeError(f"Login failed for {username}: {response.text}")

    return str(response.json()["access_token"])


def assert_security_headers(response) -> None:
    """Validate required security headers."""

    required_headers = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "no-referrer",
    }

    for header_name, expected_value in required_headers.items():
        actual_value = response.headers.get(header_name)

        if actual_value != expected_value:
            raise RuntimeError(
                f"{header_name} header beklenen değerde değil: {actual_value}"
            )


def main() -> None:
    """Run API security smoke checks."""

    cleanup_test_data()
    create_test_users()

    client = TestClient(app)

    try:
        root_response = client.get("/")

        if root_response.status_code != 200:
            raise RuntimeError("Root endpoint beklenen 200 cevabını vermedi.")

        assert_security_headers(root_response)

        unauth_me_response = client.get("/api/v1/auth/me")

        if unauth_me_response.status_code != 401:
            raise RuntimeError("/auth/me token olmadan 401 dönmeliydi.")

        invalid_token_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        if invalid_token_response.status_code != 401:
            raise RuntimeError("/auth/me geçersiz token ile 401 dönmeliydi.")

        db_health_no_token = client.get("/api/v1/db/health")

        if db_health_no_token.status_code != 401:
            raise RuntimeError("/db/health token olmadan 401 dönmeliydi.")

        staff_token = login_and_get_token(client, STAFF_USERNAME)
        db_health_staff = client.get(
            "/api/v1/db/health",
            headers={"Authorization": f"Bearer {staff_token}"},
        )

        if db_health_staff.status_code != 403:
            raise RuntimeError("/db/health staff için 403 dönmeliydi.")

        admin_token = login_and_get_token(client, SUPER_ADMIN_USERNAME)
        db_health_admin = client.get(
            "/api/v1/db/health",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        if db_health_admin.status_code != 200:
            raise RuntimeError("/db/health super_admin için 200 dönmeliydi.")

        assert_security_headers(db_health_admin)

        if "password_hash" in db_health_admin.text:
            raise RuntimeError("API response password_hash sızdırıyor.")

        print("HTTP security header kontrolü başarılı.")
        print("Unauthorized endpoint kontrolü başarılı.")
        print("Invalid token kontrolü başarılı.")
        print("Protected db health endpoint kontrolü başarılı.")
        print("API güvenlik temel kontrolü başarılı.")
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    main()
