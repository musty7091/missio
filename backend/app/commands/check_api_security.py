from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.business import Business
from app.models.login_attempt import LoginAttempt
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.auth_service import create_user_with_password, get_utc_now


SUPER_ADMIN_USERNAME = "missio_api_security_admin"
STAFF_USERNAME = "missio_api_security_staff"
BUSINESS_SLUG = "api-security-business-test"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete records created by this command."""

    db = SessionLocal()

    try:
        usernames = [
            normalize_username(SUPER_ADMIN_USERNAME),
            normalize_username(STAFF_USERNAME),
        ]

        business = (
            db.execute(select(Business).where(Business.slug == BUSINESS_SLUG))
            .scalars()
            .one_or_none()
        )
        business_id = business.id if business is not None else None

        users = (
            db.execute(select(User).where(User.username.in_(usernames)))
            .scalars()
            .all()
        )
        user_ids = [user.id for user in users]

        if business_id is not None:
            db.execute(delete(AuditLog).where(AuditLog.business_id == business_id))
            db.execute(delete(User).where(User.business_id == business_id))

        if user_ids:
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))

        for username in usernames:
            db.execute(delete(AuditLog).where(AuditLog.detail.like(f"%{username}%")))
            db.execute(delete(LoginAttempt).where(LoginAttempt.username == username))

        db.execute(delete(User).where(User.username.in_(usernames)))

        if business_id is not None:
            db.execute(delete(Business).where(Business.id == business_id))

        db.commit()
    finally:
        db.close()


def create_test_business(db) -> Business:
    """Create business for API security checks."""

    now = get_utc_now()

    business = Business(
        name="Missio API Security Business",
        slug=BUSINESS_SLUG,
        logo_path=None,
        owner_name="Missio API Security Business Owner",
        phone=None,
        email="missio.api.security.business@example.com",
        address=None,
        timezone="Europe/Istanbul",
        default_theme="dark",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db.add(business)
    db.flush()
    db.refresh(business)

    return business


def create_test_users() -> None:
    """Create local users for API security checks."""

    db = SessionLocal()

    try:
        business = create_test_business(db)

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
            business_id=business.id,
            email="missio.api.security.staff@example.com",
            is_active=True,
        )
        db.commit()
    finally:
        db.close()


def login_and_get_token(
    client: TestClient,
    *,
    username: str,
    business_slug: str | None = None,
) -> str:
    """Login and return access token."""

    payload = {
        "username": username,
        "password": TEST_PASSWORD,
    }

    if business_slug is not None:
        payload["business_slug"] = business_slug

    response = client.post(
        "/api/v1/auth/login",
        json=payload,
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


def assert_business_user_requires_slug(client: TestClient) -> None:
    """Validate business user cannot login without business_slug."""

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": STAFF_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    if response.status_code != 401:
        raise RuntimeError(
            "Business kullanıcısı business_slug olmadan login olamamalıydı. "
            f"Gelen HTTP {response.status_code}: {response.text}"
        )

    if "password_hash" in response.text:
        raise RuntimeError("Slug olmadan login response password_hash sızdırıyor.")


def assert_business_user_me_response(
    client: TestClient,
    *,
    access_token: str,
) -> None:
    """Validate business scoped staff user session response."""

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Staff /auth/me beklenen 200 yerine {response.status_code} döndü: "
            f"{response.text}"
        )

    data = response.json()

    if data.get("username") != STAFF_USERNAME:
        raise RuntimeError("Staff /auth/me username bilgisi hatalı.")

    if data.get("role") != "staff":
        raise RuntimeError("Staff /auth/me role bilgisi hatalı.")

    if data.get("business_id") is None:
        raise RuntimeError("Staff /auth/me business_id boş dönmemeli.")

    if "password_hash" in response.text:
        raise RuntimeError("Staff /auth/me response password_hash sızdırıyor.")


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

        assert_business_user_requires_slug(client)

        staff_token = login_and_get_token(
            client,
            username=STAFF_USERNAME,
            business_slug=BUSINESS_SLUG,
        )
        assert_business_user_me_response(client, access_token=staff_token)

        db_health_staff = client.get(
            "/api/v1/db/health",
            headers={"Authorization": f"Bearer {staff_token}"},
        )

        if db_health_staff.status_code != 403:
            raise RuntimeError("/db/health staff için 403 dönmeliydi.")

        admin_token = login_and_get_token(
            client,
            username=SUPER_ADMIN_USERNAME,
        )
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
        print("Business user business_slug zorunluluğu kontrolü başarılı.")
        print("Business user /auth/me kontrolü başarılı.")
        print("Protected db health endpoint kontrolü başarılı.")
        print("API güvenlik temel kontrolü başarılı.")
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    main()
