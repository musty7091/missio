from __future__ import annotations

from sqlalchemy import delete

import app.models  # noqa: F401
from app.core.tokens import create_access_token
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.user import User
from app.services.access_control_service import (
    BusinessScopeError,
    BusinessUserManagementPermissionError,
    RolePermissionError,
    UserRecordAccessError,
    ensure_business_admin_access,
    ensure_business_scope,
    ensure_business_user_management_access,
    ensure_can_create_business_user_role,
    ensure_staff_task_access,
    ensure_user_record_access,
    require_roles,
)
from app.services.auth_service import create_user_with_password, get_utc_now
from app.services.session_user_service import (
    AuthenticatedUserMismatchError,
    get_authenticated_user_from_token,
)


TEST_BUSINESS_SLUG = "missio-access-control-test"
OTHER_BUSINESS_SLUG = "missio-access-control-other-test"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete test users and businesses created by this command."""

    db = SessionLocal()

    try:
        businesses = (
            db.query(Business)
            .filter(Business.slug.in_([TEST_BUSINESS_SLUG, OTHER_BUSINESS_SLUG]))
            .all()
        )
        business_ids = [business.id for business in businesses]

        if business_ids:
            db.execute(delete(User).where(User.business_id.in_(business_ids)))

        db.execute(delete(User).where(User.username.like("access_%")))

        if business_ids:
            db.execute(delete(Business).where(Business.id.in_(business_ids)))

        db.commit()
    finally:
        db.close()


def create_test_business(
    db,
    *,
    name: str,
    slug: str,
    email: str,
) -> Business:
    """Create test business."""

    now = get_utc_now()
    business = Business(
        name=name,
        slug=slug,
        logo_path=None,
        owner_name="Missio",
        phone=None,
        email=email,
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


def assert_permission_denied(
    func,
    expected_error_type: type[Exception],
    message: str,
) -> None:
    """Assert an access control call is denied with expected error."""

    try:
        func()
    except expected_error_type:
        print(message)
        return

    raise RuntimeError(f"Beklenen yetki reddi oluşmadı: {message}")


def main() -> None:
    """Run access control checks against local database."""

    cleanup_test_data()
    db = SessionLocal()

    try:
        business = create_test_business(
            db,
            name="Missio Access Control Test",
            slug=TEST_BUSINESS_SLUG,
            email="access-control@example.com",
        )
        other_business = create_test_business(
            db,
            name="Missio Access Control Other Test",
            slug=OTHER_BUSINESS_SLUG,
            email="access-control-other@example.com",
        )

        super_admin = create_user_with_password(
            db=db,
            full_name="Access Super Admin",
            username="access_super_admin",
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
        )
        boss = create_user_with_password(
            db=db,
            full_name="Access Boss",
            username="access_boss",
            password=TEST_PASSWORD,
            role="boss",
            business_id=business.id,
        )
        business_owner = create_user_with_password(
            db=db,
            full_name="Access Business Owner",
            username="access_business_owner",
            password=TEST_PASSWORD,
            role="business_owner",
            business_id=business.id,
        )
        manager = create_user_with_password(
            db=db,
            full_name="Access Manager",
            username="access_manager",
            password=TEST_PASSWORD,
            role="manager",
            business_id=business.id,
        )
        staff = create_user_with_password(
            db=db,
            full_name="Access Staff",
            username="access_staff",
            password=TEST_PASSWORD,
            role="staff",
            business_id=business.id,
        )
        other_staff = create_user_with_password(
            db=db,
            full_name="Access Other Staff",
            username="access_other_staff",
            password=TEST_PASSWORD,
            role="staff",
            business_id=business.id,
        )

        db.commit()
        db.refresh(super_admin)
        db.refresh(boss)
        db.refresh(business_owner)
        db.refresh(manager)
        db.refresh(staff)
        db.refresh(other_staff)
        db.refresh(business)
        db.refresh(other_business)

        staff_token = create_access_token(
            subject=str(staff.id),
            role=staff.role,
            business_id=staff.business_id,
        )
        resolved_staff = get_authenticated_user_from_token(db=db, token=staff_token)

        if resolved_staff.id != staff.id:
            raise RuntimeError("Token kullanıcı çözümleme hatalı.")

        mismatch_token = create_access_token(
            subject=str(staff.id),
            role="manager",
            business_id=staff.business_id,
        )

        try:
            get_authenticated_user_from_token(db=db, token=mismatch_token)
        except AuthenticatedUserMismatchError:
            print("Token rol eşleşme kontrolü başarılı.")
        else:
            raise RuntimeError("Rolü uyuşmayan token kabul edildi.")

        require_roles(super_admin, ["super_admin"])
        require_roles(boss, ["boss", "manager"])

        assert_permission_denied(
            lambda: require_roles(staff, ["boss"]),
            RolePermissionError,
            "Rol yetki reddi kontrolü başarılı.",
        )

        ensure_business_scope(staff, business.id)
        ensure_business_scope(super_admin, business.id)

        assert_permission_denied(
            lambda: ensure_business_scope(staff, business.id + 999),
            BusinessScopeError,
            "Business scope reddi kontrolü başarılı.",
        )

        ensure_user_record_access(staff, staff)
        ensure_user_record_access(boss, staff)
        ensure_user_record_access(super_admin, staff)

        assert_permission_denied(
            lambda: ensure_user_record_access(staff, other_staff),
            UserRecordAccessError,
            "Personel başka personel kaydı reddi başarılı.",
        )

        ensure_staff_task_access(
            staff,
            task_business_id=business.id,
            assigned_to_user_id=staff.id,
        )
        ensure_staff_task_access(
            manager,
            task_business_id=business.id,
            assigned_to_user_id=staff.id,
        )
        ensure_staff_task_access(
            boss,
            task_business_id=business.id,
            assigned_to_user_id=staff.id,
        )
        ensure_staff_task_access(
            super_admin,
            task_business_id=business.id,
            assigned_to_user_id=staff.id,
        )

        assert_permission_denied(
            lambda: ensure_staff_task_access(
                staff,
                task_business_id=business.id,
                assigned_to_user_id=other_staff.id,
            ),
            UserRecordAccessError,
            "Personel başka görev erişimi reddi başarılı.",
        )

        ensure_business_admin_access(super_admin, business.id)
        ensure_business_admin_access(boss, business.id)
        ensure_business_admin_access(business_owner, business.id)

        assert_permission_denied(
            lambda: ensure_business_admin_access(manager, business.id),
            RolePermissionError,
            "Manager işletme ayarı yönetimi reddi başarılı.",
        )

        assert_permission_denied(
            lambda: ensure_business_admin_access(staff, business.id),
            RolePermissionError,
            "Staff işletme ayarı yönetimi reddi başarılı.",
        )

        ensure_business_user_management_access(super_admin, business.id)
        ensure_business_user_management_access(boss, business.id)
        ensure_business_user_management_access(business_owner, business.id)
        ensure_business_user_management_access(manager, business.id)

        assert_permission_denied(
            lambda: ensure_business_user_management_access(staff, business.id),
            RolePermissionError,
            "Staff kullanıcı yönetimi reddi başarılı.",
        )

        for target_role in ["boss", "business_owner", "manager", "staff"]:
            ensure_can_create_business_user_role(
                super_admin,
                target_business_id=business.id,
                target_role=target_role,
            )

        assert_permission_denied(
            lambda: ensure_can_create_business_user_role(
                super_admin,
                target_business_id=business.id,
                target_role="super_admin",
            ),
            BusinessUserManagementPermissionError,
            "Business user olarak super_admin oluşturma reddi başarılı.",
        )

        ensure_can_create_business_user_role(
            boss,
            target_business_id=business.id,
            target_role="manager",
        )
        ensure_can_create_business_user_role(
            boss,
            target_business_id=business.id,
            target_role="staff",
        )

        assert_permission_denied(
            lambda: ensure_can_create_business_user_role(
                boss,
                target_business_id=business.id,
                target_role="boss",
            ),
            BusinessUserManagementPermissionError,
            "Boss başka boss oluşturma reddi başarılı.",
        )

        assert_permission_denied(
            lambda: ensure_can_create_business_user_role(
                boss,
                target_business_id=other_business.id,
                target_role="staff",
            ),
            BusinessScopeError,
            "Boss başka işletmede kullanıcı oluşturma reddi başarılı.",
        )

        ensure_can_create_business_user_role(
            manager,
            target_business_id=business.id,
            target_role="staff",
        )

        assert_permission_denied(
            lambda: ensure_can_create_business_user_role(
                manager,
                target_business_id=business.id,
                target_role="manager",
            ),
            BusinessUserManagementPermissionError,
            "Manager başka manager oluşturma reddi başarılı.",
        )

        assert_permission_denied(
            lambda: ensure_can_create_business_user_role(
                manager,
                target_business_id=business.id,
                target_role="boss",
            ),
            BusinessUserManagementPermissionError,
            "Manager boss oluşturma reddi başarılı.",
        )

        assert_permission_denied(
            lambda: ensure_can_create_business_user_role(
                staff,
                target_business_id=business.id,
                target_role="staff",
            ),
            BusinessUserManagementPermissionError,
            "Staff kullanıcı oluşturma reddi başarılı.",
        )

        print("Business admin yetki matrisi kontrolü başarılı.")
        print("Business user yönetimi yetki matrisi kontrolü başarılı.")
        print("Business user rol oluşturma matrisi kontrolü başarılı.")
        print("Access control temel kontrolü başarılı.")
    finally:
        db.close()
        cleanup_test_data()


if __name__ == "__main__":
    main()
