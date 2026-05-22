from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.business import Business
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.auth_service import (
    create_login_token_for_user,
    create_user_with_password,
)
from app.services.business_service import create_business_with_owner
from app.services.user_management_service import create_business_user


SUPER_ADMIN_USERNAME = "business_user_role_change_admin"
BUSINESS_SLUG = "business-user-role-change-test"
OTHER_BUSINESS_SLUG = "business-user-role-change-other-test"

OWNER_USERNAME = "business_user_role_change_owner"
OTHER_OWNER_USERNAME = "business_user_role_change_other_owner"
MANAGER_USERNAME = "business_user_role_change_manager"
STAFF_USERNAME = "business_user_role_change_staff"
STAFF_ACTOR_USERNAME = "business_user_role_change_staff_actor"

TEST_PASSWORD = "Missio.2026!"


def get_all_test_usernames() -> list[str]:
    """Return all usernames used by this command."""

    return [
        SUPER_ADMIN_USERNAME,
        OWNER_USERNAME,
        OTHER_OWNER_USERNAME,
        MANAGER_USERNAME,
        STAFF_USERNAME,
        STAFF_ACTOR_USERNAME,
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
    """Assert sensitive fields are not leaked in response."""

    forbidden_terms = [
        "password_hash",
        "password",
        "new_password",
    ]

    for forbidden_term in forbidden_terms:
        if forbidden_term in response_text:
            raise RuntimeError(
                f"{context} response hassas alan sızdırıyor: {forbidden_term}"
            )


def assert_role_change_response_is_safe(
    data: dict[str, Any],
    *,
    expected_user_id: int,
    expected_business_id: int,
    expected_username: str,
    expected_role: str,
    context: str,
) -> None:
    """Validate safe role change response."""

    if set(data.keys()) != {"user", "message"}:
        raise RuntimeError(f"{context} response ana alanları hatalı: {data}")

    if data.get("message") != "İşletme kullanıcısı rolü güncellendi.":
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
        raise RuntimeError(
            f"{context} role bilgisi hatalı. "
            f"Beklenen: {expected_role}, Gelen: {user_data.get('role')}"
        )


def create_test_data() -> dict[str, User | Business]:
    """Create users and businesses required by role change endpoint checks."""

    db = SessionLocal()

    try:
        super_admin = create_user_with_password(
            db=db,
            full_name="Business User Role Change Admin",
            username=SUPER_ADMIN_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="business.user.role.change.admin@example.com",
            is_active=True,
        )
        db.commit()
        db.refresh(super_admin)

        result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Role Change Test",
            business_slug=BUSINESS_SLUG,
            owner_full_name="Business User Role Change Owner",
            owner_username=OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.role.change.owner@example.com",
            business_email="business.user.role.change@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user role change endpoint check",
        )

        other_result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Role Change Other Test",
            business_slug=OTHER_BUSINESS_SLUG,
            owner_full_name="Business User Role Change Other Owner",
            owner_username=OTHER_OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.role.change.other.owner@example.com",
            business_email="business.user.role.change.other@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user role change endpoint check",
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
            full_name="Business User Role Change Manager",
            username=MANAGER_USERNAME,
            password=TEST_PASSWORD,
            role="manager",
            email="business.user.role.change.manager@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user role change endpoint check",
        )

        staff_user = create_business_user(
            db=db,
            current_user=result.owner_user,
            business=result.business,
            full_name="Business User Role Change Staff",
            username=STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="business.user.role.change.staff@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user role change endpoint check",
        )

        staff_actor_user = create_business_user(
            db=db,
            current_user=result.owner_user,
            business=result.business,
            full_name="Business User Role Change Staff Actor",
            username=STAFF_ACTOR_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="business.user.role.change.staff.actor@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user role change endpoint check",
        )

        db.commit()
        db.refresh(super_admin)
        db.refresh(result.business)
        db.refresh(result.owner_user)
        db.refresh(other_result.business)
        db.refresh(other_result.owner_user)
        db.refresh(manager_user)
        db.refresh(staff_user)
        db.refresh(staff_actor_user)

        return {
            "super_admin": super_admin,
            "business": result.business,
            "other_business": other_result.business,
            "boss_user": result.owner_user,
            "other_business_user": other_result.owner_user,
            "manager_user": manager_user,
            "staff_user": staff_user,
            "staff_actor_user": staff_actor_user,
        }
    finally:
        db.close()


def assert_role_change_audit_log_exists(
    *,
    expected_business_id: int,
    expected_count_at_least: int,
) -> None:
    """Validate role change audit logs exist and are safe."""

    db = SessionLocal()

    try:
        audit_logs = (
            db.execute(
                select(AuditLog).where(
                    AuditLog.business_id == expected_business_id,
                    AuditLog.action == "business.user_role_changed",
                )
            )
            .scalars()
            .all()
        )

        if len(audit_logs) < expected_count_at_least:
            raise RuntimeError(
                "business.user_role_changed audit log eksik. "
                f"Beklenen en az: {expected_count_at_least}, Gelen: {len(audit_logs)}"
            )

        for audit_log in audit_logs:
            detail = audit_log.detail or ""

            forbidden_values = [
                TEST_PASSWORD,
                "password",
                "password_hash",
                "new_password",
            ]

            for forbidden_value in forbidden_values:
                if forbidden_value in detail:
                    raise RuntimeError(
                        "Role change audit log hassas bilgi sızdırıyor: "
                        f"{forbidden_value}"
                    )
    finally:
        db.close()


def main() -> None:
    """Run business user role change endpoint smoke checks."""

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
        staff_actor_user = test_data["staff_actor_user"]

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

        if not isinstance(staff_actor_user, User):
            raise RuntimeError("staff_actor_user test verisi hatalı.")

        change_staff_url = (
            f"/api/v1/businesses/{business.id}/users/{staff_user.id}/change-role"
        )
        change_manager_url = (
            f"/api/v1/businesses/{business.id}/users/{manager_user.id}/change-role"
        )
        change_boss_url = (
            f"/api/v1/businesses/{business.id}/users/{boss_user.id}/change-role"
        )
        change_other_business_user_with_wrong_business_url = (
            f"/api/v1/businesses/{business.id}/users/"
            f"{other_business_user.id}/change-role"
        )
        change_other_business_url = (
            f"/api/v1/businesses/{other_business.id}/users/"
            f"{other_business_user.id}/change-role"
        )

        super_admin_headers = build_auth_headers(super_admin)
        boss_headers = build_auth_headers(boss_user)
        manager_headers = build_auth_headers(manager_user)
        staff_headers = build_auth_headers(staff_actor_user)

        no_token_response = client.post(
            change_staff_url,
            json={"role": "manager"},
        )

        if no_token_response.status_code != 401:
            raise RuntimeError(
                "Role change endpoint token olmadan 401 dönmeliydi. "
                f"Gelen HTTP {no_token_response.status_code}: {no_token_response.text}"
            )

        invalid_role_response = client.post(
            change_staff_url,
            headers=super_admin_headers,
            json={"role": "boss"},
        )

        if invalid_role_response.status_code != 422:
            raise RuntimeError(
                "Role change endpoint boss rolü için 422 dönmeliydi. "
                f"Gelen HTTP {invalid_role_response.status_code}: "
                f"{invalid_role_response.text}"
            )

        assert_no_secret_fields(
            invalid_role_response.text,
            context="Invalid role change",
        )

        super_admin_role_change_response = client.post(
            change_staff_url,
            headers=super_admin_headers,
            json={"role": "manager"},
        )

        if super_admin_role_change_response.status_code != 200:
            raise RuntimeError(
                "Super admin staff kullanıcısını manager yaparken 200 almalıydı. "
                f"Gelen HTTP {super_admin_role_change_response.status_code}: "
                f"{super_admin_role_change_response.text}"
            )

        assert_no_secret_fields(
            super_admin_role_change_response.text,
            context="Super admin role change",
        )

        assert_role_change_response_is_safe(
            super_admin_role_change_response.json(),
            expected_user_id=staff_user.id,
            expected_business_id=business.id,
            expected_username=STAFF_USERNAME,
            expected_role="manager",
            context="Super admin role change",
        )

        boss_role_change_response = client.post(
            change_staff_url,
            headers=boss_headers,
            json={"role": "staff"},
        )

        if boss_role_change_response.status_code != 200:
            raise RuntimeError(
                "Boss manager kullanıcısını staff yaparken 200 almalıydı. "
                f"Gelen HTTP {boss_role_change_response.status_code}: "
                f"{boss_role_change_response.text}"
            )

        assert_no_secret_fields(
            boss_role_change_response.text,
            context="Boss role change",
        )

        assert_role_change_response_is_safe(
            boss_role_change_response.json(),
            expected_user_id=staff_user.id,
            expected_business_id=business.id,
            expected_username=STAFF_USERNAME,
            expected_role="staff",
            context="Boss role change",
        )

        same_role_response = client.post(
            change_staff_url,
            headers=super_admin_headers,
            json={"role": "staff"},
        )

        if same_role_response.status_code != 400:
            raise RuntimeError(
                "Aynı role değiştirme isteği 400 dönmeliydi. "
                f"Gelen HTTP {same_role_response.status_code}: "
                f"{same_role_response.text}"
            )

        manager_role_change_response = client.post(
            change_staff_url,
            headers=manager_headers,
            json={"role": "manager"},
        )

        if manager_role_change_response.status_code != 403:
            raise RuntimeError(
                "Manager role change endpointinden 403 almalıydı. "
                f"Gelen HTTP {manager_role_change_response.status_code}: "
                f"{manager_role_change_response.text}"
            )

        staff_role_change_response = client.post(
            change_staff_url,
            headers=staff_headers,
            json={"role": "manager"},
        )

        if staff_role_change_response.status_code != 403:
            raise RuntimeError(
                "Staff role change endpointinden 403 almalıydı. "
                f"Gelen HTTP {staff_role_change_response.status_code}: "
                f"{staff_role_change_response.text}"
            )

        boss_target_role_change_response = client.post(
            change_boss_url,
            headers=super_admin_headers,
            json={"role": "staff"},
        )

        if boss_target_role_change_response.status_code != 403:
            raise RuntimeError(
                "Patron hedef kullanıcının rolü bu endpoint ile "
                "değiştirilememeli ve 403 dönmeliydi. "
                f"Gelen HTTP {boss_target_role_change_response.status_code}: "
                f"{boss_target_role_change_response.text}"
            )

        boss_changes_other_business_response = client.post(
            change_other_business_url,
            headers=boss_headers,
            json={"role": "staff"},
        )

        if boss_changes_other_business_response.status_code != 403:
            raise RuntimeError(
                "Boss başka işletmede rol değiştirirken 403 almalıydı. "
                f"Gelen HTTP {boss_changes_other_business_response.status_code}: "
                f"{boss_changes_other_business_response.text}"
            )

        cross_business_user_response = client.post(
            change_other_business_user_with_wrong_business_url,
            headers=super_admin_headers,
            json={"role": "staff"},
        )

        if cross_business_user_response.status_code != 403:
            raise RuntimeError(
                "Başka işletmeye ait user_id yanlış business_id altında "
                "403 dönmeliydi. "
                f"Gelen HTTP {cross_business_user_response.status_code}: "
                f"{cross_business_user_response.text}"
            )

        missing_user_response = client.post(
            f"/api/v1/businesses/{business.id}/users/999999999/change-role",
            headers=super_admin_headers,
            json={"role": "manager"},
        )

        if missing_user_response.status_code != 404:
            raise RuntimeError(
                "Olmayan user_id rol değişikliği 404 dönmeliydi. "
                f"Gelen HTTP {missing_user_response.status_code}: "
                f"{missing_user_response.text}"
            )

        assert_role_change_audit_log_exists(
            expected_business_id=business.id,
            expected_count_at_least=2,
        )

        print("Business user role change token kontrolü başarılı.")
        print("Business user role change geçersiz rol reddi başarılı.")
        print("Super admin business user role change kontrolü başarılı.")
        print("Boss business user role change kontrolü başarılı.")
        print("Manager business user role change reddi başarılı.")
        print("Staff business user role change reddi başarılı.")
        print("Business user role change cross-business reddi başarılı.")
        print("Business user role change audit log kontrolü başarılı.")
        print("Business user role change endpoint smoke testi başarılı.")
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    main()