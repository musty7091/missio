from __future__ import annotations

import argparse

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.roles import UserRole
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.auth_service import create_user_with_password


DEFAULT_FULL_NAME = "Missio Super Admin"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "Missio.2026!"
DEFAULT_EMAIL = "admin@missio.local"


def get_existing_user_by_username(db, *, username: str) -> User | None:
    """Return user by normalized username."""

    normalized_username = normalize_username(username)

    return (
        db.execute(
            select(User).where(
                User.business_id.is_(None),
                User.username == normalized_username,
            )
        )
        .scalars()
        .first()
    )


def main() -> None:
    """Create or reactivate a local super admin user."""

    parser = argparse.ArgumentParser(
        description="Missio local geliştirme ortamı için super_admin oluşturur."
    )
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        help=f"Kullanıcı adı. Varsayılan: {DEFAULT_USERNAME}",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help=f"Şifre. Varsayılan: {DEFAULT_PASSWORD}",
    )
    parser.add_argument(
        "--full-name",
        default=DEFAULT_FULL_NAME,
        help=f"Ad soyad. Varsayılan: {DEFAULT_FULL_NAME}",
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_EMAIL,
        help=f"E-posta. Varsayılan: {DEFAULT_EMAIL}",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        existing_user = get_existing_user_by_username(
            db=db,
            username=args.username,
        )

        if existing_user is not None:
            existing_user.role = UserRole.SUPER_ADMIN.value
            existing_user.business_id = None
            existing_user.is_active = True
            existing_user.full_name = args.full_name.strip()
            existing_user.email = args.email.strip().lower() if args.email else None

            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            print("[OK] Mevcut kullanıcı super_admin olarak güncellendi.")
            print(f"[OK] id: {existing_user.id}")
            print(f"[OK] username: {existing_user.username}")
            print(f"[OK] role: {existing_user.role}")
            print("[UYARI] Mevcut kullanıcının şifresi değiştirilmedi.")
            return

        user = create_user_with_password(
            db=db,
            full_name=args.full_name,
            username=args.username,
            password=args.password,
            role=UserRole.SUPER_ADMIN.value,
            business_id=None,
            email=args.email,
            is_active=True,
        )

        db.commit()
        db.refresh(user)

        print("[OK] Local super_admin kullanıcı oluşturuldu.")
        print(f"[OK] id: {user.id}")
        print(f"[OK] username: {user.username}")
        print(f"[OK] role: {user.role}")
        print(f"[OK] email: {user.email}")
        print("")
        print("[GİRİŞ BİLGİLERİ]")
        print(f"username: {normalize_username(args.username)}")
        print(f"password: {args.password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()