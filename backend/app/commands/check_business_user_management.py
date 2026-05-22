from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.business import Business
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.access_control_service import (
    BusinessScopeError,
    BusinessUserManagementPermissionError,
)
from app.services.auth_service import create_user_with_password
from app.services.business_service import create_business_with_owner
from app.services.user_management_service import (
    BusinessUserManagementError,
    InvalidBusinessUserRoleError,
    create_business_user,
)


SUPER_ADMIN_USERNAME = "business_user_mgmt_super_admin"
BUSINESS_SLUG = "business-user-mgmt-test"
OTHER_BUSINESS_SLUG = "business-user-mgmt-other-test"

OWNER_USERNAME = "business_user_mgmt_owner"
OTHER_OWNER_USERNAME = "business_user_mgmt_other_owner"

SUPER_ADMIN_CREATED_BOSS_USERNAME = "business_user_mgmt_admin_created_boss"
SUPER_ADMIN_CREATED_BUSINESS_OWNER_USERNAME = (
    "business_user_mgmt_admin_created_business_owner"
)
SUPER_ADMIN_CREATED_MANAGER_USERNAME = "business_user_mgmt_admin_created_manager"
SUPER_ADMIN_CREATED_STAFF_USERNAME = "business_user_mgmt_admin_created_staff"

BOSS_CREATED_MANAGER_USERNAME = "business_user_mgmt_boss_created_manager"
BOSS_CREATED_STAFF_USERNAME = "business_user_mgmt_boss_created_staff"
MANAGER_CREATED_STAFF_USERNAME = "business_user_mgmt_manager_created_staff"

DENIED_BOSS_USERNAME = "business_user_mgmt_denied_boss"
DENIED_MANAGER_USERNAME = "business_user_mgmt_denied_manager"
DENIED_STAFF_USERNAME = "business_user_mgmt_denied_staff"
DENIED_SUPER_ADMIN_USERNAME = "business_user_mgmt_denied_super_admin"
DENIED_OTHER_BUSINESS_STAFF_USERNAME = "business_user_mgmt_denied_other_staff"

TEST_PASSWORD = "Missio.2026!"

ExpectedError: TypeAlias = type[Exception] | tuple[type[Exception], ...]


def get_all_test_usernames() -> list[str]:
    """Return all usernames used by this command."""

    return [
        SUPER_ADMIN_USERNAME,
        OWNER_USERNAME,
        OTHER_OWNER_USERNAME,
        SUPER_ADMIN_CREATED_BOSS_USERNAME,
        SUPER_ADMIN_CREATED_BUSINESS_OWNER_USERNAME,
        SUPER_ADMIN_CREATED_MANAGER_USERNAME,
        SUPER_ADMIN_CREATED_STAFF_USERNAME,
        BOSS_CREATED_MANAGER_USERNAME,
        BOSS_CREATED_STAFF_USERNAME,
        MANAGER_CREATED_STAFF_USERNAME,
        DENIED_BOSS_USERNAME,
        DENIED_MANAGER_USERNAME,
        DENIED_STAFF_USERNAME,
        DENIED_SUPER_ADMIN_USERNAME,
        DENIED_OTHER_BUSINESS_STAFF_USERNAME,
    ]


def cleanup_test_data() -> None:
    """Delete test data created by this command."""

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


def assert_denied(
    action: Callable[[], object],
    *,
    expected_error: ExpectedError,
    success_message: str,
) -> None:
    """Assert action is denied with expected error type."""

    try:
        action()
    except expected_error:
        print(success_message)
        return

    raise RuntimeError(f"Beklenen yetki reddi oluşmadı: {success_message}")


def assert_created_user(
    user: User,
    *,
    expected_business_id: int,
    expected_role: str,
    expected_username: str,
) -> None:
    """Validate created business user."""

    if user.business_id != expected_business_id:
        raise RuntimeError(
            f"{expected_username} business_id hatalı. "
            f"Beklenen: {expected_business_id}, Gelen: {user.business_id}"
        )

    if user.role != expected_role:
        raise RuntimeError(
            f"{expected_username} rolü hatalı. "
            f"Beklenen: {expected_role}, Gelen: {user.role}"
        )

    if user.username != normalize_username(expected_username):
        raise RuntimeError(f"{expected_username} username normalize bilgisi hatalı.")


def main() -> None:
    """Run business user management checks."""

    cleanup_test_data()
    db = SessionLocal()

    try:
        super_admin = create_user_with_password(
            db=db,
            full_name="Business User Management Super Admin",
            username=SUPER_ADMIN_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="business.user.management.admin@example.com",
            is_active=True,
        )
        db.commit()
        db.refresh(super_admin)

        result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Management Test",
            business_slug=BUSINESS_SLUG,
            owner_full_name="Business User Management Owner",
            owner_username=OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.management.owner@example.com",
            business_email="business.user.management@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )

        other_result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business User Management Other Test",
            business_slug=OTHER_BUSINESS_SLUG,
            owner_full_name="Business User Management Other Owner",
            owner_username=OTHER_OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.user.management.other.owner@example.com",
            business_email="business.user.management.other@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )
        db.commit()
        db.refresh(result.business)
        db.refresh(result.owner_user)
        db.refresh(other_result.business)

        super_admin_created_boss = create_business_user(
            db=db,
            current_user=super_admin,
            business=result.business,
            full_name="Super Admin Created Boss",
            username=SUPER_ADMIN_CREATED_BOSS_USERNAME,
            password=TEST_PASSWORD,
            role="boss",
            email="admin.created.boss@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )
        super_admin_created_business_owner = create_business_user(
            db=db,
            current_user=super_admin,
            business=result.business,
            full_name="Super Admin Created Business Owner",
            username=SUPER_ADMIN_CREATED_BUSINESS_OWNER_USERNAME,
            password=TEST_PASSWORD,
            role="boss",
            email="admin.created.business.owner@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )
        super_admin_created_manager = create_business_user(
            db=db,
            current_user=super_admin,
            business=result.business,
            full_name="Super Admin Created Manager",
            username=SUPER_ADMIN_CREATED_MANAGER_USERNAME,
            password=TEST_PASSWORD,
            role="manager",
            email="admin.created.manager@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )
        super_admin_created_staff = create_business_user(
            db=db,
            current_user=super_admin,
            business=result.business,
            full_name="Super Admin Created Staff",
            username=SUPER_ADMIN_CREATED_STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="admin.created.staff@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )

        boss_created_manager = create_business_user(
            db=db,
            current_user=result.owner_user,
            business=result.business,
            full_name="Boss Created Manager",
            username=BOSS_CREATED_MANAGER_USERNAME,
            password=TEST_PASSWORD,
            role="manager",
            email="boss.created.manager@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )
        boss_created_staff = create_business_user(
            db=db,
            current_user=result.owner_user,
            business=result.business,
            full_name="Boss Created Staff",
            username=BOSS_CREATED_STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="boss.created.staff@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )

        manager_created_staff = create_business_user(
            db=db,
            current_user=boss_created_manager,
            business=result.business,
            full_name="Manager Created Staff",
            username=MANAGER_CREATED_STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="manager.created.staff@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )

        db.commit()

        created_users = [
            (super_admin_created_boss, "boss", SUPER_ADMIN_CREATED_BOSS_USERNAME),
            (
                super_admin_created_business_owner,
                "boss",
                SUPER_ADMIN_CREATED_BUSINESS_OWNER_USERNAME,
            ),
            (
                super_admin_created_manager,
                "manager",
                SUPER_ADMIN_CREATED_MANAGER_USERNAME,
            ),
            (super_admin_created_staff, "staff", SUPER_ADMIN_CREATED_STAFF_USERNAME),
            (boss_created_manager, "manager", BOSS_CREATED_MANAGER_USERNAME),
            (boss_created_staff, "staff", BOSS_CREATED_STAFF_USERNAME),
            (manager_created_staff, "staff", MANAGER_CREATED_STAFF_USERNAME),
        ]

        for user, expected_role, expected_username in created_users:
            db.refresh(user)
            assert_created_user(
                user,
                expected_business_id=result.business.id,
                expected_role=expected_role,
                expected_username=expected_username,
            )

        assert_denied(
            lambda: create_business_user(
                db=db,
                current_user=super_admin,
                business=result.business,
                full_name="Denied Super Admin",
                username=DENIED_SUPER_ADMIN_USERNAME,
                password=TEST_PASSWORD,
                role="super_admin",
                email="denied.super.admin@example.com",
            ),
            expected_error=InvalidBusinessUserRoleError,
            success_message="Business user olarak super_admin oluşturma reddi başarılı.",
        )

        assert_denied(
            lambda: create_business_user(
                db=db,
                current_user=result.owner_user,
                business=result.business,
                full_name="Denied Boss",
                username=DENIED_BOSS_USERNAME,
                password=TEST_PASSWORD,
                role="boss",
                email="denied.boss@example.com",
            ),
            expected_error=BusinessUserManagementPermissionError,
            success_message="Boss tarafından boss oluşturma reddi başarılı.",
        )

        assert_denied(
            lambda: create_business_user(
                db=db,
                current_user=boss_created_manager,
                business=result.business,
                full_name="Denied Manager",
                username=DENIED_MANAGER_USERNAME,
                password=TEST_PASSWORD,
                role="manager",
                email="denied.manager@example.com",
            ),
            expected_error=BusinessUserManagementPermissionError,
            success_message="Manager tarafından manager oluşturma reddi başarılı.",
        )

        assert_denied(
            lambda: create_business_user(
                db=db,
                current_user=boss_created_manager,
                business=result.business,
                full_name="Denied Boss From Manager",
                username=DENIED_BOSS_USERNAME,
                password=TEST_PASSWORD,
                role="boss",
                email="denied.boss.from.manager@example.com",
            ),
            expected_error=BusinessUserManagementPermissionError,
            success_message="Manager tarafından boss oluşturma reddi başarılı.",
        )

        assert_denied(
            lambda: create_business_user(
                db=db,
                current_user=boss_created_staff,
                business=result.business,
                full_name="Denied Staff",
                username=DENIED_STAFF_USERNAME,
                password=TEST_PASSWORD,
                role="staff",
                email="denied.staff@example.com",
            ),
            expected_error=BusinessUserManagementPermissionError,
            success_message="Staff tarafından kullanıcı oluşturma reddi başarılı.",
        )

        assert_denied(
            lambda: create_business_user(
                db=db,
                current_user=result.owner_user,
                business=other_result.business,
                full_name="Denied Other Business Staff",
                username=DENIED_OTHER_BUSINESS_STAFF_USERNAME,
                password=TEST_PASSWORD,
                role="staff",
                email="denied.other.business.staff@example.com",
            ),
            expected_error=BusinessScopeError,
            success_message="Boss tarafından başka işletmede kullanıcı oluşturma reddi başarılı.",
        )

        db.rollback()

        audit_logs = db.execute(
            select(AuditLog).where(AuditLog.business_id == result.business.id),
        ).scalars().all()
        business_user_created_count = sum(
            1
            for audit_log in audit_logs
            if audit_log.action == "business.user_created"
        )

        if business_user_created_count < len(created_users):
            raise RuntimeError("business.user_created audit log eksik.")

        print("Super admin business user oluşturma kontrolü başarılı.")
        print("Boss business user oluşturma kontrolü başarılı.")
        print("Manager business user oluşturma kontrolü başarılı.")
        print("Yetkisiz business user oluşturma reddi kontrolü başarılı.")
        print("Business user audit log kontrolü başarılı.")
        print("Business user management temel kontrolü başarılı.")
    finally:
        db.close()
        cleanup_test_data()


if __name__ == "__main__":
    main()
