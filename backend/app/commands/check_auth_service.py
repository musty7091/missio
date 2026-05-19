from __future__ import annotations

from sqlalchemy import delete

import app.models  # noqa: F401
from app.core.tokens import decode_access_token
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.login_attempt import LoginAttempt
from app.models.user import User
from app.repositories.user_repository import get_user_by_username, normalize_username
from app.services.auth_service import (
    authenticate_user,
    create_login_token_for_user,
    create_user_with_password,
)


TEST_USERNAME = "missio_auth_test_admin"
TEST_PASSWORD = "Missio.2026!"


def delete_test_user_if_exists() -> None:
    """Delete previous test user and related security records if they exist."""

    db = SessionLocal()

    try:
        normalized_username = normalize_username(TEST_USERNAME)
        user = get_user_by_username(
            db=db,
            username=normalized_username,
            business_id=None,
        )
        user_id = user.id if user is not None else None

        if user_id is not None:
            db.execute(
                delete(AuditLog).where(AuditLog.user_id == user_id),
            )

        db.execute(
            delete(AuditLog).where(AuditLog.detail.like(f"%{normalized_username}%")),
        )
        db.execute(
            delete(LoginAttempt).where(LoginAttempt.username == normalized_username),
        )
        db.execute(
            delete(User).where(User.username == normalized_username),
        )
        db.commit()
    finally:
        db.close()


def main() -> None:
    """Run auth service check against the local database."""

    delete_test_user_if_exists()

    db = SessionLocal()

    try:
        user = create_user_with_password(
            db=db,
            full_name="Missio Test Admin",
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="missio.auth.test@example.com",
            is_active=True,
        )
        db.commit()
        db.refresh(user)

        if TEST_PASSWORD in user.password_hash:
            raise RuntimeError("Şifre hash içinde açık görünüyor.")

        authenticated_user = authenticate_user(
            db=db,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            business_id=None,
        )
        db.commit()
        db.refresh(authenticated_user)

        if authenticated_user.last_login_at is None:
            raise RuntimeError("last_login_at güncellenmedi.")

        login_token = create_login_token_for_user(authenticated_user)
        payload = decode_access_token(login_token.access_token)

        if payload.subject != str(authenticated_user.id):
            raise RuntimeError("Token subject bilgisi hatalı.")

        if payload.role != "super_admin":
            raise RuntimeError("Token rol bilgisi hatalı.")

        if payload.business_id is not None:
            raise RuntimeError("Super admin token business_id boş olmalı.")

        print("Auth service kullanıcı oluşturma kontrolü başarılı.")
        print("Auth service kullanıcı doğrulama kontrolü başarılı.")
        print("Auth service token üretme kontrolü başarılı.")
    finally:
        db.close()
        delete_test_user_if_exists()

    print("Auth service temel kontrolü başarılı.")


if __name__ == "__main__":
    main()
