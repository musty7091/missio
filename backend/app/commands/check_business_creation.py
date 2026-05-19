from __future__ import annotations

from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.business import Business
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.auth_service import create_user_with_password
from app.services.business_service import DuplicateBusinessSlugError, create_business_with_owner


SUPER_ADMIN_USERNAME = "business_service_super_admin"
OWNER_USERNAME = "business_service_owner"
BUSINESS_SLUG = "business-service-test"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete test data created by this command."""

    db = SessionLocal()

    try:
        business = db.query(Business).filter(Business.slug == BUSINESS_SLUG).one_or_none()
        business_id = business.id if business is not None else None
        usernames = [normalize_username(SUPER_ADMIN_USERNAME), normalize_username(OWNER_USERNAME), "duplicate_owner"]
        users = db.execute(select(User).where(User.username.in_(usernames))).scalars().all()
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
    """Run business creation service checks."""

    cleanup_test_data()
    db = SessionLocal()

    try:
        super_admin = create_user_with_password(
            db=db,
            full_name="Business Service Super Admin",
            username=SUPER_ADMIN_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="business.service.admin@example.com",
            is_active=True,
        )
        db.commit()
        db.refresh(super_admin)

        result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name="Business Service Test",
            business_slug=BUSINESS_SLUG,
            owner_full_name="Business Service Owner",
            owner_username=OWNER_USERNAME,
            owner_password=TEST_PASSWORD,
            owner_email="business.service.owner@example.com",
            business_email="business.service@example.com",
            business_phone="0533 000 00 00",
            ip_address="127.0.0.1",
            user_agent="Missio business creation check",
        )
        db.commit()
        db.refresh(result.business)
        db.refresh(result.owner_user)

        if result.owner_user.business_id != result.business.id:
            raise RuntimeError("Owner user business_id hatalı.")

        if result.owner_user.role != "boss":
            raise RuntimeError("Owner user rolü boss olmalı.")

        audit_logs = db.execute(select(AuditLog).where(AuditLog.business_id == result.business.id)).scalars().all()
        actions = {audit_log.action for audit_log in audit_logs}

        if "business.created" not in actions:
            raise RuntimeError("business.created audit log eksik.")

        if "business.owner_created" not in actions:
            raise RuntimeError("business.owner_created audit log eksik.")

        try:
            create_business_with_owner(
                db=db,
                current_user=super_admin,
                business_name="Duplicate Business",
                business_slug=BUSINESS_SLUG,
                owner_full_name="Duplicate Owner",
                owner_username="duplicate_owner",
                owner_password=TEST_PASSWORD,
            )
        except DuplicateBusinessSlugError:
            db.rollback()
            print("Duplicate business slug reddi başarılı.")
        else:
            raise RuntimeError("Duplicate business slug kabul edildi.")

        print("İşletme oluşturma kontrolü başarılı.")
        print("İşletme sahibi oluşturma kontrolü başarılı.")
        print("Business audit log kontrolü başarılı.")
        print("Business creation temel kontrolü başarılı.")
    finally:
        db.close()
        cleanup_test_data()


if __name__ == "__main__":
    main()
