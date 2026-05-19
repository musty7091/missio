from __future__ import annotations

import argparse
import getpass
import sys

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.repositories.user_repository import get_user_by_username
from app.services.access_control_service import RolePermissionError
from app.services.auth_service import WeakPasswordError
from app.services.business_service import (
    BusinessServiceError,
    DuplicateBusinessSlugError,
    create_business_with_owner,
)


def build_parser() -> argparse.ArgumentParser:
    """Build command argument parser."""

    parser = argparse.ArgumentParser(description="Create a business and first boss account.")
    parser.add_argument("--super-admin-username", required=True)
    parser.add_argument("--business-name", required=True)
    parser.add_argument("--business-slug", required=True)
    parser.add_argument("--business-phone", required=False)
    parser.add_argument("--business-email", required=False)
    parser.add_argument("--business-address", required=False)
    parser.add_argument("--owner-full-name", required=True)
    parser.add_argument("--owner-username", required=True)
    parser.add_argument("--owner-email", required=False)
    parser.add_argument("--owner-password", required=False)
    parser.add_argument("--yes", action="store_true")

    return parser


def get_owner_password(value: str | None) -> str:
    """Read owner password from argument or secure prompt."""

    if value is not None:
        return value

    password = getpass.getpass("İşletme sahibi şifresi: ")
    password_repeat = getpass.getpass("İşletme sahibi şifresi tekrar: ")

    if password != password_repeat:
        raise BusinessServiceError("Şifreler eşleşmiyor.")

    return password


def confirm_creation(business_name: str, owner_username: str, yes: bool) -> None:
    """Confirm operation."""

    if yes:
        return

    print("")
    print("İşletme ve ilk patron hesabı oluşturulacak.")
    print(f"İşletme: {business_name}")
    print(f"Patron kullanıcı adı: {owner_username}")
    print("")
    confirmation = input("Devam etmek için EVET yazın: ").strip()

    if confirmation != "EVET":
        raise BusinessServiceError("İşlem iptal edildi.")


def main() -> None:
    """Create business and owner account."""

    parser = build_parser()
    args = parser.parse_args()
    db = SessionLocal()

    try:
        current_user = get_user_by_username(db=db, username=args.super_admin_username, business_id=None)

        if current_user is None:
            raise BusinessServiceError("Super admin kullanıcı bulunamadı.")

        owner_password = get_owner_password(args.owner_password)
        confirm_creation(business_name=args.business_name, owner_username=args.owner_username, yes=args.yes)

        result = create_business_with_owner(
            db=db,
            current_user=current_user,
            business_name=args.business_name,
            business_slug=args.business_slug,
            business_phone=args.business_phone,
            business_email=args.business_email,
            business_address=args.business_address,
            owner_full_name=args.owner_full_name,
            owner_username=args.owner_username,
            owner_password=owner_password,
            owner_email=args.owner_email,
            ip_address="business-cli",
            user_agent="Missio create business command",
        )
        db.commit()
        db.refresh(result.business)
        db.refresh(result.owner_user)

        print("İşletme ve patron hesabı başarıyla oluşturuldu.")
        print(f"Business ID: {result.business.id}")
        print(f"Business Slug: {result.business.slug}")
        print(f"Owner User ID: {result.owner_user.id}")
        print(f"Owner Username: {result.owner_user.username}")
    except WeakPasswordError as exc:
        db.rollback()
        print("Şifre güvenlik politikasına uygun değil:")
        for error in exc.errors:
            print(f"- {error}")
        sys.exit(1)
    except DuplicateBusinessSlugError as exc:
        db.rollback()
        print(f"İşletme slug hatası: {exc}")
        sys.exit(1)
    except RolePermissionError as exc:
        db.rollback()
        print(f"Yetki hatası: {exc}")
        sys.exit(1)
    except BusinessServiceError as exc:
        db.rollback()
        print(f"İşletme oluşturma hatası: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
