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


SUPER_ADMIN_USERNAME = "missio_auth_endpoint_test"
ACTIVE_BUSINESS_SLUG = "auth-endpoint-business-test"
PASSIVE_BUSINESS_SLUG = "auth-endpoint-passive-business-test"

BOSS_USERNAME = "auth_endpoint_business_boss"
MANAGER_USERNAME = "auth_endpoint_business_manager"
STAFF_USERNAME = "auth_endpoint_business_staff"
PASSIVE_BUSINESS_BOSS_USERNAME = "auth_endpoint_passive_business_boss"

TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete test records created by this command."""

    db = SessionLocal()

    try:
        usernames = [
            normalize_username(SUPER_ADMIN_USERNAME),
            normalize_username(BOSS_USERNAME),
            normalize_username(MANAGER_USERNAME),
            normalize_username(STAFF_USERNAME),
            normalize_username(PASSIVE_BUSINESS_BOSS_USERNAME),
        ]

        businesses = (
            db.execute(
                select(Business).where(
                    Business.slug.in_(
                        [
                            ACTIVE_BUSINESS_SLUG,
                            PASSIVE_BUSINESS_SLUG,
                        ]
                    )
                )
            )
            .scalars()
            .all()
        )
        business_ids = [business.id for business in businesses]

        users = (
            db.execute(select(User).where(User.username.in_(usernames)))
            .scalars()
            .all()
        )
        user_ids = [user.id for user in users]

        if business_ids:
            db.execute(delete(AuditLog).where(AuditLog.business_id.in_(business_ids)))

        if user_ids:
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))

        for username in usernames:
            db.execute(delete(AuditLog).where(AuditLog.detail.like(f"%{username}%")))
            db.execute(delete(LoginAttempt).where(LoginAttempt.username == username))

        db.execute(
            delete(AuditLog).where(
                AuditLog.detail.like("%invalid_business_slug%")
            )
        )
        db.execute(
            delete(AuditLog).where(
                AuditLog.detail.like("%inactive_business%")
            )
        )

        if business_ids:
            db.execute(delete(User).where(User.business_id.in_(business_ids)))

        db.execute(delete(User).where(User.username.in_(usernames)))

        if business_ids:
            db.execute(delete(Business).where(Business.id.in_(business_ids)))

        db.commit()
    finally:
        db.close()


def create_business(
    db,
    *,
    name: str,
    slug: str,
    owner_name: str,
    email: str,
    is_active: bool,
) -> Business:
    """Create a test business."""

    now = get_utc_now()

    business = Business(
        name=name,
        slug=slug,
        logo_path=None,
        owner_name=owner_name,
        phone=None,
        email=email,
        address=None,
        timezone="Europe/Istanbul",
        default_theme="dark",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )

    db.add(business)
    db.flush()
    db.refresh(business)

    return business


def create_test_data() -> None:
    """Create local users and businesses for auth endpoint checks."""

    db = SessionLocal()

    try:
        create_user_with_password(
            db=db,
            full_name="Missio Auth Endpoint Test",
            username=SUPER_ADMIN_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="missio.auth.endpoint@example.com",
            is_active=True,
        )

        active_business = create_business(
            db=db,
            name="Auth Endpoint Business Test",
            slug=ACTIVE_BUSINESS_SLUG,
            owner_name="Auth Endpoint Boss",
            email="auth.endpoint.business@example.com",
            is_active=True,
        )

        passive_business = create_business(
            db=db,
            name="Auth Endpoint Passive Business Test",
            slug=PASSIVE_BUSINESS_SLUG,
            owner_name="Auth Endpoint Passive Boss",
            email="auth.endpoint.passive.business@example.com",
            is_active=False,
        )

        create_user_with_password(
            db=db,
            full_name="Auth Endpoint Business Boss",
            username=BOSS_USERNAME,
            password=TEST_PASSWORD,
            role="boss",
            business_id=active_business.id,
            email="auth.endpoint.business.boss@example.com",
            is_active=True,
        )

        create_user_with_password(
            db=db,
            full_name="Auth Endpoint Business Manager",
            username=MANAGER_USERNAME,
            password=TEST_PASSWORD,
            role="manager",
            business_id=active_business.id,
            email="auth.endpoint.business.manager@example.com",
            is_active=True,
        )

        create_user_with_password(
            db=db,
            full_name="Auth Endpoint Business Staff",
            username=STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            business_id=active_business.id,
            email="auth.endpoint.business.staff@example.com",
            is_active=True,
        )

        create_user_with_password(
            db=db,
            full_name="Auth Endpoint Passive Business Boss",
            username=PASSIVE_BUSINESS_BOSS_USERNAME,
            password=TEST_PASSWORD,
            role="boss",
            business_id=passive_business.id,
            email="auth.endpoint.passive.business.boss@example.com",
            is_active=True,
        )

        db.commit()
    finally:
        db.close()


def assert_login_response_is_safe(login_data: dict[str, object]) -> str:
    """Validate login response and return access token."""

    access_token = login_data.get("access_token")

    if not access_token:
        raise RuntimeError("Login response access_token içermiyor.")

    if not isinstance(access_token, str):
        raise RuntimeError("Login response access_token metin formatında değil.")

    if login_data.get("token_type") != "bearer":
        raise RuntimeError("Login response token_type bearer değil.")

    if "password_hash" in login_data:
        raise RuntimeError("Login response password_hash sızdırıyor.")

    return access_token


def assert_me_response_is_safe(
    me_data: dict[str, object],
    *,
    expected_username: str,
    expected_role: str,
    business_id_should_exist: bool,
) -> None:
    """Validate /auth/me response for a logged-in user."""

    if me_data.get("username") != expected_username:
        raise RuntimeError(
            f"Me endpoint username bilgisi hatalı. Beklenen: {expected_username}"
        )

    if me_data.get("role") != expected_role:
        raise RuntimeError(
            f"Me endpoint role bilgisi hatalı. Beklenen: {expected_role}"
        )

    if business_id_should_exist and me_data.get("business_id") is None:
        raise RuntimeError("Me endpoint business_id boş dönmemeli.")

    if not business_id_should_exist and me_data.get("business_id") is not None:
        raise RuntimeError("Super admin business_id None olmalıydı.")

    if "password_hash" in me_data:
        raise RuntimeError("Me endpoint password_hash sızdırıyor.")


def login_and_assert_me(
    client: TestClient,
    *,
    payload: dict[str, str],
    expected_username: str,
    expected_role: str,
    business_id_should_exist: bool,
) -> dict[str, object]:
    """Login with payload and validate /auth/me."""

    login_response = client.post(
        "/api/v1/auth/login",
        json=payload,
    )

    if login_response.status_code != 200:
        raise RuntimeError(
            f"Login endpoint beklenen 200 yerine "
            f"{login_response.status_code} döndü: {login_response.text}"
        )

    access_token = assert_login_response_is_safe(login_response.json())

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

    assert_me_response_is_safe(
        me_data,
        expected_username=expected_username,
        expected_role=expected_role,
        business_id_should_exist=business_id_should_exist,
    )

    return me_data


def assert_login_rejected(
    client: TestClient,
    *,
    payload: dict[str, str],
    expected_status_code: int,
    message: str,
) -> None:
    """Validate rejected login response."""

    response = client.post(
        "/api/v1/auth/login",
        json=payload,
    )

    if response.status_code != expected_status_code:
        raise RuntimeError(
            f"{message} Beklenen HTTP {expected_status_code}, "
            f"gelen HTTP {response.status_code}: {response.text}"
        )

    response_data = response.json()

    if "password_hash" in response.text:
        raise RuntimeError("Hatalı login response password_hash sızdırıyor.")

    if "detail" not in response_data:
        raise RuntimeError("Hatalı login response detail alanı içermiyor.")


def assert_login_failure_recorded(
    *,
    username: str,
    failure_reason: str,
    business_id_should_exist: bool,
) -> None:
    """Validate login attempt and audit log were recorded for rejected login."""

    normalized_username = normalize_username(username)
    db = SessionLocal()

    try:
        login_attempt = (
            db.execute(
                select(LoginAttempt)
                .where(LoginAttempt.username == normalized_username)
                .where(LoginAttempt.was_successful.is_(False))
                .where(LoginAttempt.failure_reason == failure_reason)
                .order_by(LoginAttempt.id.desc())
            )
            .scalars()
            .first()
        )

        if login_attempt is None:
            raise RuntimeError(
                f"{failure_reason} için login_attempt kaydı bulunamadı."
            )

        if business_id_should_exist and login_attempt.business_id is None:
            raise RuntimeError(
                f"{failure_reason} için login_attempt business_id boş olmamalı."
            )

        if not business_id_should_exist and login_attempt.business_id is not None:
            raise RuntimeError(
                f"{failure_reason} için login_attempt business_id boş olmalı."
            )

        audit_log = (
            db.execute(
                select(AuditLog)
                .where(AuditLog.action == "auth.login_failed")
                .where(AuditLog.detail.like(f"%{normalized_username}%"))
                .where(AuditLog.detail.like(f"%{failure_reason}%"))
                .order_by(AuditLog.id.desc())
            )
            .scalars()
            .first()
        )

        if audit_log is None:
            raise RuntimeError(
                f"{failure_reason} için auth.login_failed audit kaydı bulunamadı."
            )

        if business_id_should_exist and audit_log.business_id is None:
            raise RuntimeError(
                f"{failure_reason} için audit business_id boş olmamalı."
            )

        if not business_id_should_exist and audit_log.business_id is not None:
            raise RuntimeError(
                f"{failure_reason} için audit business_id boş olmalı."
            )
    finally:
        db.close()


def main() -> None:
    """Run auth endpoint smoke checks."""

    cleanup_test_data()
    create_test_data()

    client = TestClient(app)

    try:
        login_and_assert_me(
            client,
            payload={
                "username": SUPER_ADMIN_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_username=SUPER_ADMIN_USERNAME,
            expected_role="super_admin",
            business_id_should_exist=False,
        )

        boss_me_data = login_and_assert_me(
            client,
            payload={
                "business_slug": ACTIVE_BUSINESS_SLUG,
                "username": BOSS_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_username=BOSS_USERNAME,
            expected_role="boss",
            business_id_should_exist=True,
        )

        manager_me_data = login_and_assert_me(
            client,
            payload={
                "business_slug": ACTIVE_BUSINESS_SLUG,
                "username": MANAGER_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_username=MANAGER_USERNAME,
            expected_role="manager",
            business_id_should_exist=True,
        )

        staff_me_data = login_and_assert_me(
            client,
            payload={
                "business_slug": ACTIVE_BUSINESS_SLUG,
                "username": STAFF_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_username=STAFF_USERNAME,
            expected_role="staff",
            business_id_should_exist=True,
        )

        active_business_id = boss_me_data.get("business_id")

        if manager_me_data.get("business_id") != active_business_id:
            raise RuntimeError("Manager business_id boss business_id ile eşleşmiyor.")

        if staff_me_data.get("business_id") != active_business_id:
            raise RuntimeError("Staff business_id boss business_id ile eşleşmiyor.")

        assert_login_rejected(
            client,
            payload={
                "username": BOSS_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_status_code=401,
            message="Boss business_slug olmadan login olamamalı.",
        )

        assert_login_rejected(
            client,
            payload={
                "username": MANAGER_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_status_code=401,
            message="Manager business_slug olmadan login olamamalı.",
        )

        assert_login_rejected(
            client,
            payload={
                "username": STAFF_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_status_code=401,
            message="Staff business_slug olmadan login olamamalı.",
        )

        assert_login_rejected(
            client,
            payload={
                "business_slug": "wrong-business-slug",
                "username": BOSS_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_status_code=401,
            message="Hatalı işletme slug güvenli şekilde reddedilmedi.",
        )
        assert_login_failure_recorded(
            username=BOSS_USERNAME,
            failure_reason="invalid_business_slug",
            business_id_should_exist=False,
        )

        assert_login_rejected(
            client,
            payload={
                "business_slug": PASSIVE_BUSINESS_SLUG,
                "username": PASSIVE_BUSINESS_BOSS_USERNAME,
                "password": TEST_PASSWORD,
            },
            expected_status_code=401,
            message="Pasif işletme kullanıcısı login olamamalı.",
        )
        assert_login_failure_recorded(
            username=PASSIVE_BUSINESS_BOSS_USERNAME,
            failure_reason="inactive_business",
            business_id_should_exist=True,
        )

        assert_login_rejected(
            client,
            payload={
                "username": SUPER_ADMIN_USERNAME,
                "password": "Wrong.2026!",
            },
            expected_status_code=401,
            message="Hatalı şifre güvenli şekilde reddedilmedi.",
        )

        print("Super admin login endpoint başarı kontrolü başarılı.")
        print("Boss business login endpoint başarı kontrolü başarılı.")
        print("Manager business login endpoint başarı kontrolü başarılı.")
        print("Staff business login endpoint başarı kontrolü başarılı.")
        print("Business kullanıcılarının slug olmadan reddi başarılı.")
        print("Business slug güvenli hata cevabı kontrolü başarılı.")
        print("Business slug audit kayıt kontrolü başarılı.")
        print("Pasif işletme login reddi kontrolü başarılı.")
        print("Pasif işletme audit kayıt kontrolü başarılı.")
        print("Me endpoint token, role ve business_id kontrolü başarılı.")
        print("Güvenli hata cevabı kontrolü başarılı.")
        print("Auth endpoint temel kontrolü başarılı.")
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    main()
