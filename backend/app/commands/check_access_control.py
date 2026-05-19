from __future__ import annotations

from sqlalchemy import delete

import app.models  # noqa: F401
from app.core.tokens import create_access_token
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.user import User
from app.services.access_control_service import (
    BusinessScopeError,
    RolePermissionError,
    UserRecordAccessError,
    ensure_business_scope,
    ensure_user_record_access,
    require_roles,
)
from app.services.auth_service import create_user_with_password, get_utc_now
from app.services.session_user_service import (
    AuthenticatedUserMismatchError,
    get_authenticated_user_from_token,
)


TEST_BUSINESS_SLUG = "missio-access-control-test"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete test users and business created by this command."""

    db = SessionLocal()

    try:
        business = (
            db.query(Business)
            .filter(Business.slug == TEST_BUSINESS_SLUG)
            .one_or_none()
        )

        if business is not None:
            db.execute(delete(User).where(User.business_id == business.id))
            db.delete(business)

        db.execute(delete(User).where(User.username.like("access_%")))
        db.commit()
    finally:
        db.close()


def create_test_business(db) -> Business:
    """Create test business."""

    now = get_utc_now()
    business = Business(
        name="Missio Access Control Test",
        slug=TEST_BUSINESS_SLUG,
        logo_path=None,
        owner_name="Missio",
        phone=None,
        email="access-control@example.com",
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


def main() -> None:
    """Run access control checks against local database."""

    cleanup_test_data()
    db = SessionLocal()

    try:
        business = create_test_business(db)

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
        db.refresh(staff)
        db.refresh(other_staff)

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

        try:
            require_roles(staff, ["boss"])
        except RolePermissionError:
            print("Rol yetki reddi kontrolü başarılı.")
        else:
            raise RuntimeError("Personel patron yetkisi aldı.")

        ensure_business_scope(staff, business.id)
        ensure_business_scope(super_admin, business.id)

        try:
            ensure_business_scope(staff, business.id + 999)
        except BusinessScopeError:
            print("Business scope reddi kontrolü başarılı.")
        else:
            raise RuntimeError("Personel başka işletme kapsamına erişti.")

        ensure_user_record_access(staff, staff)
        ensure_user_record_access(boss, staff)
        ensure_user_record_access(super_admin, staff)

        try:
            ensure_user_record_access(staff, other_staff)
        except UserRecordAccessError:
            print("Personel başka personel kaydı reddi başarılı.")
        else:
            raise RuntimeError("Personel başka personel kaydına erişti.")

        print("Access control temel kontrolü başarılı.")
    finally:
        db.close()
        cleanup_test_data()


if __name__ == "__main__":
    main()
