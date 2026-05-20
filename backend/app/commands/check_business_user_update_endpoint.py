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


SUPER_ADMIN_USERNAME = "business_user_update_admin"
BUSINESS_SLUG = "business-user-update-test"
OTHER_BUSINESS_SLUG = "business-user-update-other-test"

OWNER_USERNAME = "business_user_update_owner"
OTHER_OWNER_USERNAME = "business_user_update_other_owner"
MANAGER_USERNAME = "business_user_update_manager"
STAFF_USERNAME = "business_user_update_staff"

TEST_PASSWORD = "Missio.2026!"


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


def assert_no_password_hash(response_text: str, *, context: str) -> None:
    """Assert password_hash is not leaked in response."""

    if "password_hash" in response_text:
        raise RuntimeError(f"{context} response password_hash sızdırıyor.")


def assert_updated_response_is_safe(
    data: dict[str, Any],
    *,
    expected_user_id: int,
    expected_business_id: int,
    expected_full_name: str,
    expected_email: str | None,
    expected_theme_preference: str | None,
    expected_is_active: bool,
    context: str,
) -> None:
    """Validate safe update endpoint response."""

    if set(data.keys()) != {"user", "message"}:
        raise RuntimeError(f"{context} response ana alanları hatalı: {data}")

    if data.get("message") != "İşletme kullanıcısı güncellendi.":
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

    if user_data.get("full_name") != expected_full_name:
        raise RuntimeError(f"{context} full_name güncellenmedi.")

    if user_data.get("email") != expected_email:
        raise RuntimeError(f"{context} email güncellenmedi.")

    if user_data.get("theme_preference") != expected_theme_preference:
        raise RuntimeError(f"{context} theme_preference güncellenmedi.")

    if user_data.get("is_active") != expected_is_active:
        raise RuntimeError(f"{context} is_active güncellenmedi.")


def create_test_data() -> dict[str, User | Business]:
    """Create users and businesses required by update endpoint checks."""

    db = SessionLocal()

    try:
        super_admin = create_user_with_password(
            db=db,
            full_name="Business User Update Admin",
            username=SUPER_ADMIN_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="business.user.update.admin@example.com",
            is_active=True,
        )
        db.commit()
        db.refresh(super_admin)

        result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Update Test",
            business_slug=BUSINESS_SLUG,
            owner_full_name="Business User Update Owner",
            owner_username=OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.update.owner@example.com",
            business_email="business.user.update@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user update endpoint check",
        )

        other_result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Update Other Test",
            business_slug=OTHER_BUSINESS_SLUG,
            owner_full_name="Business User Update Other Owner",
            owner_username=OTHER_OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.update.other.owner@example.com",
            business_email="business.user.update.other@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user update endpoint check",
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
            full_name="Business User Update Manager",
            username=MANAGER_USERNAME,
            password=TEST_PASSWORD,
            role="manager",
            email="business.user.update.manager@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user update endpoint check",
        )

        staff_user = create_business_user(
            db=db,
            current_user=result.owner_user,
            business=result.business,
            full_name="Business User Update Staff",
            username=STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="business.user.update.staff@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user update endpoint check",
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


def main() -> None:
    """Run business user update endpoint smoke checks."""

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

        update_staff_url = (
            f"/api/v1/businesses/{business.id}/users/{staff_user.id}"
        )
        update_manager_url = (
            f"/api/v1/businesses/{business.id}/users/{manager_user.id}"
        )
        update_other_business_user_with_wrong_business_url = (
            f"/api/v1/businesses/{business.id}/users/{other_business_user.id}"
        )
        update_other_business_url = (
            f"/api/v1/businesses/{other_business.id}/users/{other_business_user.id}"
        )

        super_admin_headers = build_auth_headers(super_admin)
        boss_headers = build_auth_headers(boss_user)
        manager_headers = build_auth_headers(manager_user)
        staff_headers = build_auth_headers(staff_user)

        no_token_response = client.patch(
            update_staff_url,
            json={"full_name": "No Token Update"},
        )

        if no_token_response.status_code != 401:
            raise RuntimeError(
                "Update endpoint token olmadan 401 dönmeliydi. "
                f"Gelen HTTP {no_token_response.status_code}: {no_token_response.text}"
            )

        empty_body_response = client.patch(
            update_staff_url,
            headers=super_admin_headers,
            json={},
        )

        if empty_body_response.status_code != 422:
            raise RuntimeError(
                "Update endpoint boş body ile 422 dönmeliydi. "
                f"Gelen HTTP {empty_body_response.status_code}: "
                f"{empty_body_response.text}"
            )

        super_admin_update_response = client.patch(
            update_staff_url,
            headers=super_admin_headers,
            json={
                "full_name": "Super Admin Updated Staff",
                "email": "super.admin.updated.staff@example.com",
                "theme_preference": "dark",
                "is_active": True,
            },
        )

        if super_admin_update_response.status_code != 200:
            raise RuntimeError(
                "Super admin staff güncellemede 200 almalıydı. "
                f"Gelen HTTP {super_admin_update_response.status_code}: "
                f"{super_admin_update_response.text}"
            )

        assert_no_password_hash(
            super_admin_update_response.text,
            context="Super admin update",
        )

        assert_updated_response_is_safe(
            super_admin_update_response.json(),
            expected_user_id=staff_user.id,
            expected_business_id=business.id,
            expected_full_name="Super Admin Updated Staff",
            expected_email="super.admin.updated.staff@example.com",
            expected_theme_preference="dark",
            expected_is_active=True,
            context="Super admin update",
        )

        boss_update_response = client.patch(
            update_manager_url,
            headers=boss_headers,
            json={
                "full_name": "Boss Updated Manager",
                "email": "boss.updated.manager@example.com",
                "theme_preference": "light",
                "is_active": True,
            },
        )

        if boss_update_response.status_code != 200:
            raise RuntimeError(
                "Boss manager güncellemede 200 almalıydı. "
                f"Gelen HTTP {boss_update_response.status_code}: "
                f"{boss_update_response.text}"
            )

        assert_no_password_hash(
            boss_update_response.text,
            context="Boss update",
        )

        assert_updated_response_is_safe(
            boss_update_response.json(),
            expected_user_id=manager_user.id,
            expected_business_id=business.id,
            expected_full_name="Boss Updated Manager",
            expected_email="boss.updated.manager@example.com",
            expected_theme_preference="light",
            expected_is_active=True,
            context="Boss update",
        )

        manager_update_response = client.patch(
            update_staff_url,
            headers=manager_headers,
            json={
                "full_name": "Manager Updated Staff",
                "email": "manager.updated.staff@example.com",
                "theme_preference": "dark",
                "is_active": True,
            },
        )

        if manager_update_response.status_code != 200:
            raise RuntimeError(
                "Manager staff güncellemede 200 almalıydı. "
                f"Gelen HTTP {manager_update_response.status_code}: "
                f"{manager_update_response.text}"
            )

        assert_no_password_hash(
            manager_update_response.text,
            context="Manager update",
        )

        assert_updated_response_is_safe(
            manager_update_response.json(),
            expected_user_id=staff_user.id,
            expected_business_id=business.id,
            expected_full_name="Manager Updated Staff",
            expected_email="manager.updated.staff@example.com",
            expected_theme_preference="dark",
            expected_is_active=True,
            context="Manager update",
        )

        staff_update_response = client.patch(
            update_staff_url,
            headers=staff_headers,
            json={"full_name": "Staff Should Not Update"},
        )

        if staff_update_response.status_code != 403:
            raise RuntimeError(
                "Staff update endpointinden 403 almalıydı. "
                f"Gelen HTTP {staff_update_response.status_code}: "
                f"{staff_update_response.text}"
            )

        manager_updates_manager_response = client.patch(
            update_manager_url,
            headers=manager_headers,
            json={"full_name": "Manager Should Not Update Manager"},
        )

        if manager_updates_manager_response.status_code != 403:
            raise RuntimeError(
                "Manager kendi seviyesindeki kullanıcıyı güncellerken "
                "403 almalıydı. "
                f"Gelen HTTP {manager_updates_manager_response.status_code}: "
                f"{manager_updates_manager_response.text}"
            )

        boss_updates_other_business_response = client.patch(
            update_other_business_url,
            headers=boss_headers,
            json={"full_name": "Boss Should Not Update Other Business"},
        )

        if boss_updates_other_business_response.status_code != 403:
            raise RuntimeError(
                "Boss başka işletmede kullanıcı güncellerken 403 almalıydı. "
                f"Gelen HTTP {boss_updates_other_business_response.status_code}: "
                f"{boss_updates_other_business_response.text}"
            )

        cross_business_user_response = client.patch(
            update_other_business_user_with_wrong_business_url,
            headers=super_admin_headers,
            json={"full_name": "Wrong Business User Update"},
        )

        if cross_business_user_response.status_code != 403:
            raise RuntimeError(
                "Başka işletmeye ait user_id yanlış business_id altında "
                "403 dönmeliydi. "
                f"Gelen HTTP {cross_business_user_response.status_code}: "
                f"{cross_business_user_response.text}"
            )

        missing_user_response = client.patch(
            f"/api/v1/businesses/{business.id}/users/999999999",
            headers=super_admin_headers,
            json={"full_name": "Missing User"},
        )

        if missing_user_response.status_code != 404:
            raise RuntimeError(
                "Olmayan user_id güncellemesi 404 dönmeliydi. "
                f"Gelen HTTP {missing_user_response.status_code}: "
                f"{missing_user_response.text}"
            )

        print("Business user update endpoint token kontrolü başarılı.")
        print("Business user update endpoint boş body kontrolü başarılı.")
        print("Super admin business user update kontrolü başarılı.")
        print("Boss business user update kontrolü başarılı.")
        print("Manager business user update kontrolü başarılı.")
        print("Staff business user update reddi başarılı.")
        print("Business user update cross-business reddi başarılı.")
        print("Business user update endpoint smoke testi başarılı.")
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    main()