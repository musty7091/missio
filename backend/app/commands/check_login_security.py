from __future__ import annotations

from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.login_attempt import LoginAttempt
from app.models.user import User
from app.repositories.user_repository import get_user_by_username, normalize_username
from app.services.auth_service import (
    AccountTemporarilyLockedError,
    InvalidCredentialsError,
    authenticate_user,
    create_login_token_for_user,
    create_user_with_password,
)


TEST_USERNAME = "missio_login_security_test"
TEST_PASSWORD = "Missio.2026!"


def cleanup_test_data() -> None:
    """Delete test data created by this command."""

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


def count_login_attempts() -> int:
    """Return login attempt count for the test username."""

    db = SessionLocal()

    try:
        statement = select(LoginAttempt).where(
            LoginAttempt.username == normalize_username(TEST_USERNAME),
        )
        return len(db.execute(statement).scalars().all())
    finally:
        db.close()


def main() -> None:
    """Run login attempt, brute-force and auth audit checks."""

    cleanup_test_data()

    db = SessionLocal()

    try:
        user = create_user_with_password(
            db=db,
            full_name="Missio Login Security Test",
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            role="super_admin",
            business_id=None,
            email="missio.login.security@example.com",
            is_active=True,
        )
        db.commit()
        db.refresh(user)

        for _ in range(5):
            try:
                authenticate_user(
                    db=db,
                    username=TEST_USERNAME,
                    password="Wrong.2026!",
                    business_id=None,
                    ip_address="127.0.0.1",
                    user_agent="Missio security check",
                )
            except InvalidCredentialsError:
                db.commit()
            else:
                raise RuntimeError("Hatalı şifre kabul edildi.")

        try:
            authenticate_user(
                db=db,
                username=TEST_USERNAME,
                password=TEST_PASSWORD,
                business_id=None,
                ip_address="127.0.0.1",
                user_agent="Missio security check",
            )
        except AccountTemporarilyLockedError:
            db.commit()
            print("Brute-force geçici kilit kontrolü başarılı.")
        else:
            raise RuntimeError("Kilitli kullanıcı login olabildi.")

        db.execute(
            delete(LoginAttempt).where(
                LoginAttempt.username == normalize_username(TEST_USERNAME),
            ),
        )
        db.commit()

        authenticated_user = authenticate_user(
            db=db,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            business_id=None,
            ip_address="127.0.0.1",
            user_agent="Missio security check",
        )
        db.commit()
        db.refresh(authenticated_user)

        if authenticated_user.last_login_at is None:
            raise RuntimeError("Başarılı login sonrası last_login_at güncellenmedi.")

        login_token = create_login_token_for_user(authenticated_user)

        if not login_token.access_token:
            raise RuntimeError("Login token üretilemedi.")

        if count_login_attempts() < 1:
            raise RuntimeError("Login attempt kaydı oluşmadı.")

        print("Başarılı login attempt kontrolü başarılı.")
        print("Auth audit log kontrolü başarılı.")
        print("Login güvenlik temel kontrolü başarılı.")
    finally:
        db.close()
        cleanup_test_data()


if __name__ == "__main__":
    main()
