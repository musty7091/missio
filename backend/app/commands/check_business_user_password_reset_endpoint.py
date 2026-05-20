from __future__ import annotations

from typing import Any

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
from app.services.auth_service import (
    create_login_token_for_user,
    create_user_with_password,
)
from app.services.business_service import create_business_with_owner
from app.services.user_management_service import create_business_user


SUPER_ADMIN_USERNAME = "business_user_password_reset_admin"
BUSINESS_SLUG = "business-user-password-reset-test"
OTHER_BUSINESS_SLUG = "business-user-password-reset-other-test"

OWNER_USERNAME = "business_user_password_reset_owner"
OTHER_OWNER_USERNAME = "business_user_password_reset_other_owner"
MANAGER_USERNAME = "business_user_password_reset_manager"
STAFF_USERNAME = "business_user_password_reset_staff"

TEST_PASSWORD = "Missio.2026!"
RESET_STAFF_PASSWORD = "ResetStaff.2026!"
RESET_MANAGER_PASSWORD = "ResetManager.2026!"
RESET_STAFF_BY_MANAGER_PASSWORD = "ResetStaffByManager.2026!"


def get_all_test_usernames() -> list[str]:
    """Return all usernames used by this command."""

    return [
        SUPER_ADMIN_USERNAME,
        OWNER_USERNAME,
        OTHER_OWNER_USERNAME,
        MANAGER_USERNAME,
        STAFF_USERNAME,
    ]


def cleanup_test_data() -> None:
    """Delete test records created by this command."""

    db = SessionLocal()

    try:
        business_slugs = [
            BUSINESS_SLUG,
            OTHER_BUSINESS_SLUG,
        ]

        businesses = (
            db.execute(select(Business).where(Business.slug.in_(business_slugs)))
            .scalars()
            .all()
        )
        business_ids = [business.id for business in businesses]

        usernames = [
            normalize_username(username)
            for username in get_all_test_usernames()
        ]

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

        if business_ids:
            db.execute(delete(User).where(User.business_id.in_(business_ids)))

        db.execute(delete(User).where(User.username.in_(usernames)))

        if business_ids:
            db.execute(delete(Business).where(Business.id.in_(business_ids)))

        db.commit()
    finally:
        db.close()


def build_auth_headers(user: User) -> dict[str, str]:
    """Build Authorization header for a user."""

    login_token = create_login_token_for_user(user)

    return {
        "Authorization": f"Bearer {login_token.access_token}",
    }


def assert_no_secret_fields(response_text: str, *, context: str) -> None:
    """Assert sensitive password fields are not leaked in response."""

    forbidden_terms = [
        "password_hash",
        "new_password",
    ]

    for forbidden_term in forbidden_terms:
        if forbidden_term in response_text:
            raise RuntimeError(
                f"{context} response hassas alan sızdırıyor: {forbidden_term}"
            )


def assert_password_reset_response_is_safe(
    data: dict[str, Any],
    *,
    expected_user_id: int,
    expected_business_id: int,
    expected_username: str,
    expected_role: str,
    context: str,
) -> None:
    """Validate safe password reset response."""

    if set(data.keys()) != {"user", "message"}:
        raise RuntimeError(f"{context} response ana alanları hatalı: {data}")

    if data.get("message") != "İşletme kullanıcısı şifresi sıfırlandı.":
        raise RuntimeError(f"{context} message alanı hatalı: {data.get('message')}")

    user_data = data.get("user")

    if not isinstance(user_data, dict):
        raise RuntimeError(f"{context} user alanı obje formatında değil.")

    expected_user_fields = {
        "id",
        "business_id",
        "full_name",
        "username",
        "email",
        "role",
        "is_active",
        "theme_preference",
    }

    if set(user_data.keys()) != expected_user_fields:
        raise RuntimeError(
            f"{context} user alanları hatalı. "
            f"Gelen alanlar: {sorted(user_data.keys())}"
        )

    if user_data.get("id") != expected_user_id:
        raise RuntimeError(f"{context} id bilgisi hatalı.")

    if user_data.get("business_id") != expected_business_id:
        raise RuntimeError(f"{context} business_id bilgisi hatalı.")

    if user_data.get("username") != normalize_username(expected_username):
        raise RuntimeError(f"{context} username bilgisi hatalı.")

    if user_data.get("role") != expected_role:
        raise RuntimeError(f"{context} role bilgisi hatalı.")


def assert_business_login_works(
    client: TestClient,
    *,
    username: str,
    password: str,
    business_slug: str,
    context: str,
) -> None:
    """Validate business user can login with given password."""

    response = client.post(
        "/api/v1/auth/login",
        json={
            "business_slug": business_slug,
            "username": username,
            "password": password,
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"{context} login başarılı olmalıydı. "
            f"Gelen HTTP {response.status_code}: {response.text}"
        )

    assert_no_secret_fields(response.text, context=f"{context} login")

    data = response.json()

    if not data.get("access_token"):
        raise RuntimeError(f"{context} login access_token döndürmedi.")

    if data.get("token_type") != "bearer":
        raise RuntimeError(f"{context} login token_type bearer değil.")


def assert_business_login_fails(
    client: TestClient,
    *,
    username: str,
    password: str,
    business_slug: str,
    context: str,
) -> None:
    """Validate business user cannot login with given password."""

    response = client.post(
        "/api/v1/auth/login",
        json={
            "business_slug": business_slug,
            "username": username,
            "password": password,
        },
    )

    if response.status_code != 401:
        raise RuntimeError(
            f"{context} login reddedilmeliydi. "
            f"Gelen HTTP {response.status_code}: {response.text}"
        )

    assert_no_secret_fields(response.text, context=f"{context} failed login")


def create_test_data() -> dict[str, User | Business]:
    """Create users and businesses required by password reset endpoint checks."""

    db = SessionLocal()

    try:
        super_admin = create_user_with_password(
            db=db,
            full_name="Business User Password Reset Admin",
            username=SUPER_ADMIN_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="business.user.password.reset.admin@example.com",
            is_active=True,
        )
        db.commit()
        db.refresh(super_admin)

        result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Password Reset Test",
            business_slug=BUSINESS_SLUG,
            owner_full_name="Business User Password Reset Owner",
            owner_username=OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.password.reset.owner@example.com",
            business_email="business.user.password.reset@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user password reset endpoint check",
        )

        other_result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Password Reset Other Test",
            business_slug=OTHER_BUSINESS_SLUG,
            owner_full_name="Business User Password Reset Other Owner",
            owner_username=OTHER_OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.password.reset.other.owner@example.com",
            business_email="business.user.password.reset.other@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user password reset endpoint check",
        )

        db.commit()
        db.refresh(result.business)
        db.refresh(result.owner_user)
        db.refresh(other_result.business)
        db.refresh(other_result.owner_user)

        manager_user = create_business_user(
            db=db,
            current_user=result.owner_user,
            business=result.business,
            full_name="Business User Password Reset Manager",
            username=MANAGER_USERNAME,
            password=TEST_PASSWORD,
            role="manager",
            email="business.user.password.reset.manager@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user password reset endpoint check",
        )

        staff_user = create_business_user(
            db=db,
            current_user=result.owner_user,
            business=result.business,
            full_name="Business User Password Reset Staff",
            username=STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="business.user.password.reset.staff@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user password reset endpoint check",
        )

        db.commit()
        db.refresh(super_admin)
        db.refresh(result.business)
        db.refresh(result.owner_user)
        db.refresh(other_result.business)
        db.refresh(other_result.owner_user)
        db.refresh(manager_user)
        db.refresh(staff_user)

        return {
            "super_admin": super_admin,
            "business": result.business,
            "other_business": other_result.business,
            "boss_user": result.owner_user,
            "other_business_user": other_result.owner_user,
            "manager_user": manager_user,
            "staff_user": staff_user,
        }
    finally:
        db.close()


def assert_password_reset_audit_log_exists(
    *,
    expected_business_id: int,
    expected_count_at_least: int,
) -> None:
    """Validate password reset audit logs exist and do not contain raw passwords."""

    db = SessionLocal()

    try:
        audit_logs = (
            db.execute(
                select(AuditLog).where(
                    AuditLog.business_id == expected_business_id,
                    AuditLog.action == "business.user_password_reset",
                )
            )
            .scalars()
            .all()
        )

        if len(audit_logs) < expected_count_at_least:
            raise RuntimeError(
                "business.user_password_reset audit log eksik. "
                f"Beklenen en az: {expected_count_at_least}, Gelen: {len(audit_logs)}"
            )

        for audit_log in audit_logs:
            detail = audit_log.detail or ""

            forbidden_values = [
                TEST_PASSWORD,
                RESET_STAFF_PASSWORD,
                RESET_MANAGER_PASSWORD,
                RESET_STAFF_BY_MANAGER_PASSWORD,
                "new_password",
                "password_hash",
            ]

            for forbidden_value in forbidden_values:
                if forbidden_value in detail:
                    raise RuntimeError(
                        "Password reset audit log hassas bilgi sızdırıyor: "
                        f"{forbidden_value}"
                    )
    finally:
        db.close()


def main() -> None:
    """Run business user password reset endpoint smoke checks."""

    cleanup_test_data()
    test_data = create_test_data()

    client = TestClient(app)

    try:
        super_admin = test_data["super_admin"]
        business = test_data["business"]
        other_business = test_data["other_business"]
        boss_user = test_data["boss_user"]
        other_business_user = test_data["other_business_user"]
        manager_user = test_data["manager_user"]
        staff_user = test_data["staff_user"]

        if not isinstance(super_admin, User):
            raise RuntimeError("super_admin test verisi hatalı.")

        if not isinstance(business, Business):
            raise RuntimeError("business test verisi hatalı.")

        if not isinstance(other_business, Business):
            raise RuntimeError("other_business test verisi hatalı.")

        if not isinstance(boss_user, User):
            raise RuntimeError("boss_user test verisi hatalı.")

        if not isinstance(other_business_user, User):
            raise RuntimeError("other_business_user test verisi hatalı.")

        if not isinstance(manager_user, User):
            raise RuntimeError("manager_user test verisi hatalı.")

        if not isinstance(staff_user, User):
            raise RuntimeError("staff_user test verisi hatalı.")

        reset_staff_url = (
            f"/api/v1/businesses/{business.id}/users/{staff_user.id}/reset-password"
        )
        reset_manager_url = (
            f"/api/v1/businesses/{business.id}/users/{manager_user.id}/reset-password"
        )
        reset_other_business_user_with_wrong_business_url = (
            f"/api/v1/businesses/{business.id}/users/"
            f"{other_business_user.id}/reset-password"
        )
        reset_other_business_url = (
            f"/api/v1/businesses/{other_business.id}/users/"
            f"{other_business_user.id}/reset-password"
        )

        super_admin_headers = build_auth_headers(super_admin)
        boss_headers = build_auth_headers(boss_user)
        manager_headers = build_auth_headers(manager_user)
        staff_headers = build_auth_headers(staff_user)

        no_token_response = client.post(
            reset_staff_url,
            json={"new_password": RESET_STAFF_PASSWORD},
        )

        if no_token_response.status_code != 401:
            raise RuntimeError(
                "Password reset endpoint token olmadan 401 dönmeliydi. "
                f"Gelen HTTP {no_token_response.status_code}: {no_token_response.text}"
            )

        weak_password_response = client.post(
            reset_staff_url,
            headers=super_admin_headers,
            json={"new_password": "123"},
        )

        if weak_password_response.status_code != 400:
            raise RuntimeError(
                "Password reset endpoint zayıf şifre ile 400 dönmeliydi. "
                f"Gelen HTTP {weak_password_response.status_code}: "
                f"{weak_password_response.text}"
            )

        assert_no_secret_fields(
            weak_password_response.text,
            context="Weak password reset",
        )

        super_admin_reset_response = client.post(
            reset_staff_url,
            headers=super_admin_headers,
            json={"new_password": RESET_STAFF_PASSWORD},
        )

        if super_admin_reset_response.status_code != 200:
            raise RuntimeError(
                "Super admin staff şifre sıfırlamada 200 almalıydı. "
                f"Gelen HTTP {super_admin_reset_response.status_code}: "
                f"{super_admin_reset_response.text}"
            )

        assert_no_secret_fields(
            super_admin_reset_response.text,
            context="Super admin password reset",
        )

        assert_password_reset_response_is_safe(
            super_admin_reset_response.json(),
            expected_user_id=staff_user.id,
            expected_business_id=business.id,
            expected_username=STAFF_USERNAME,
            expected_role="staff",
            context="Super admin password reset",
        )

        assert_business_login_fails(
            client,
            username=STAFF_USERNAME,
            password=TEST_PASSWORD,
            business_slug=BUSINESS_SLUG,
            context="Staff old password after super admin reset",
        )

        assert_business_login_works(
            client,
            username=STAFF_USERNAME,
            password=RESET_STAFF_PASSWORD,
            business_slug=BUSINESS_SLUG,
            context="Staff new password after super admin reset",
        )

        boss_reset_response = client.post(
            reset_manager_url,
            headers=boss_headers,
            json={"new_password": RESET_MANAGER_PASSWORD},
        )

        if boss_reset_response.status_code != 200:
            raise RuntimeError(
                "Boss manager şifre sıfırlamada 200 almalıydı. "
                f"Gelen HTTP {boss_reset_response.status_code}: "
                f"{boss_reset_response.text}"
            )

        assert_no_secret_fields(
            boss_reset_response.text,
            context="Boss password reset",
        )

        assert_password_reset_response_is_safe(
            boss_reset_response.json(),
            expected_user_id=manager_user.id,
            expected_business_id=business.id,
            expected_username=MANAGER_USERNAME,
            expected_role="manager",
            context="Boss password reset",
        )

        assert_business_login_works(
            client,
            username=MANAGER_USERNAME,
            password=RESET_MANAGER_PASSWORD,
            business_slug=BUSINESS_SLUG,
            context="Manager new password after boss reset",
        )

        manager_reset_response = client.post(
            reset_staff_url,
            headers=manager_headers,
            json={"new_password": RESET_STAFF_BY_MANAGER_PASSWORD},
        )

        if manager_reset_response.status_code != 200:
            raise RuntimeError(
                "Manager staff şifre sıfırlamada 200 almalıydı. "
                f"Gelen HTTP {manager_reset_response.status_code}: "
                f"{manager_reset_response.text}"
            )

        assert_no_secret_fields(
            manager_reset_response.text,
            context="Manager password reset",
        )

        assert_password_reset_response_is_safe(
            manager_reset_response.json(),
            expected_user_id=staff_user.id,
            expected_business_id=business.id,
            expected_username=STAFF_USERNAME,
            expected_role="staff",
            context="Manager password reset",
        )

        assert_business_login_works(
            client,
            username=STAFF_USERNAME,
            password=RESET_STAFF_BY_MANAGER_PASSWORD,
            business_slug=BUSINESS_SLUG,
            context="Staff new password after manager reset",
        )

        staff_reset_response = client.post(
            reset_staff_url,
            headers=staff_headers,
            json={"new_password": "StaffShouldNot.2026!"},
        )

        if staff_reset_response.status_code != 403:
            raise RuntimeError(
                "Staff password reset endpointinden 403 almalıydı. "
                f"Gelen HTTP {staff_reset_response.status_code}: "
                f"{staff_reset_response.text}"
            )

        manager_resets_manager_response = client.post(
            reset_manager_url,
            headers=manager_headers,
            json={"new_password": "ManagerShouldNot.2026!"},
        )

        if manager_resets_manager_response.status_code != 403:
            raise RuntimeError(
                "Manager kendi seviyesindeki kullanıcının şifresini "
                "sıfırlarken 403 almalıydı. "
                f"Gelen HTTP {manager_resets_manager_response.status_code}: "
                f"{manager_resets_manager_response.text}"
            )

        boss_resets_other_business_response = client.post(
            reset_other_business_url,
            headers=boss_headers,
            json={"new_password": "OtherBusiness.2026!"},
        )

        if boss_resets_other_business_response.status_code != 403:
            raise RuntimeError(
                "Boss başka işletmede şifre sıfırlarken 403 almalıydı. "
                f"Gelen HTTP {boss_resets_other_business_response.status_code}: "
                f"{boss_resets_other_business_response.text}"
            )

        cross_business_user_response = client.post(
            reset_other_business_user_with_wrong_business_url,
            headers=super_admin_headers,
            json={"new_password": "WrongBusiness.2026!"},
        )

        if cross_business_user_response.status_code != 403:
            raise RuntimeError(
                "Başka işletmeye ait user_id yanlış business_id altında "
                "403 dönmeliydi. "
                f"Gelen HTTP {cross_business_user_response.status_code}: "
                f"{cross_business_user_response.text}"
            )

        missing_user_response = client.post(
            f"/api/v1/businesses/{business.id}/users/999999999/reset-password",
            headers=super_admin_headers,
            json={"new_password": "MissingUser.2026!"},
        )

        if missing_user_response.status_code != 404:
            raise RuntimeError(
                "Olmayan user_id şifre sıfırlaması 404 dönmeliydi. "
                f"Gelen HTTP {missing_user_response.status_code}: "
                f"{missing_user_response.text}"
            )

        assert_password_reset_audit_log_exists(
            expected_business_id=business.id,
            expected_count_at_least=3,
        )

        print("Business user password reset token kontrolü başarılı.")
        print("Business user password reset zayıf şifre reddi başarılı.")
        print("Super admin business user password reset kontrolü başarılı.")
        print("Boss business user password reset kontrolü başarılı.")
        print("Manager business user password reset kontrolü başarılı.")
        print("Staff business user password reset reddi başarılı.")
        print("Business user password reset cross-business reddi başarılı.")
        print("Business user password reset yeni şifre login kontrolü başarılı.")
        print("Business user password reset audit log kontrolü başarılı.")
        print("Business user password reset endpoint smoke testi başarılı.")
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    main()