from __future__ import annotations

from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.business import Business
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.auth_service import create_user_with_password
from app.services.business_service import create_business_with_owner
from app.services.user_management_service import create_business_user


SUPER_ADMIN_USERNAME = "business_user_mgmt_super_admin"
BUSINESS_SLUG = "business-user-mgmt-test"
OWNER_USERNAME = "business_user_mgmt_owner"
MANAGER_USERNAME = "business_user_mgmt_manager"
STAFF_USERNAME = "business_user_mgmt_staff"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete test data created by this command."""

    db = SessionLocal()

    try:
        business = (
            db.query(Business)
            .filter(Business.slug == BUSINESS_SLUG)
            .one_or_none()
        )
        business_id = business.id if business is not None else None

        usernames = [
            normalize_username(SUPER_ADMIN_USERNAME),
            normalize_username(OWNER_USERNAME),
            normalize_username(MANAGER_USERNAME),
            normalize_username(STAFF_USERNAME),
        ]
        users = db.execute(
            select(User).where(User.username.in_(usernames)),
        ).scalars().all()
        user_ids = [user.id for user in users]

        if business_id is not None:
            db.execute(delete(AuditLog).where(AuditLog.business_id == business_id))
            db.execute(delete(User).where(User.business_id == business_id))

        if user_ids:
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))

        db.execute(delete(User).where(User.username.in_(usernames)))

        if business_id is not None:
            db.execute(delete(Business).where(Business.id == business_id))

        db.commit()
    finally:
        db.close()


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
        db.commit()
        db.refresh(result.business)

        manager = create_business_user(
            db=db,
            current_user=super_admin,
            business=result.business,
            full_name="Business User Management Manager",
            username=MANAGER_USERNAME,
            password=TEST_PASSWORD,
            role="manager",
            email="business.user.management.manager@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )
        staff = create_business_user(
            db=db,
            current_user=super_admin,
            business=result.business,
            full_name="Business User Management Staff",
            username=STAFF_USERNAME,
            password=TEST_PASSWORD,
            role="staff",
            email="business.user.management.staff@example.com",
            ip_address="127.0.0.1",
            user_agent="Missio business user management check",
        )
        db.commit()
        db.refresh(manager)
        db.refresh(staff)

        if manager.business_id != result.business.id:
            raise RuntimeError("Manager business_id hatalı.")

        if staff.business_id != result.business.id:
            raise RuntimeError("Staff business_id hatalı.")

        if manager.role != "manager":
            raise RuntimeError("Manager rolü hatalı.")

        if staff.role != "staff":
            raise RuntimeError("Staff rolü hatalı.")

        audit_logs = db.execute(
            select(AuditLog).where(AuditLog.business_id == result.business.id),
        ).scalars().all()
        business_user_created_count = sum(
            1
            for audit_log in audit_logs
            if audit_log.action == "business.user_created"
        )

        if business_user_created_count < 2:
            raise RuntimeError("business.user_created audit log eksik.")

        print("Manager oluşturma kontrolü başarılı.")
        print("Staff oluşturma kontrolü başarılı.")
        print("Business user audit log kontrolü başarılı.")
        print("Business user management temel kontrolü başarılı.")
    finally:
        db.close()
        cleanup_test_data()


if __name__ == "__main__":
    main()
