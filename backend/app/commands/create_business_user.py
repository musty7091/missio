from __future__ import annotations

import argparse
import getpass
import sys

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.repositories.business_repository import get_business_by_slug
from app.repositories.user_repository import get_user_by_username
from app.services.access_control_service import RolePermissionError
from app.services.auth_service import DuplicateUsernameError, WeakPasswordError
from app.services.user_management_service import (
    BusinessUserManagementError,
    InvalidBusinessUserRoleError,
    create_business_user,
)


def build_parser() -> argparse.ArgumentParser:
    """Build command argument parser."""

    parser = argparse.ArgumentParser(
        description="Create a business scoped user as super admin.",
    )
    parser.add_argument("--super-admin-username", required=True)
    parser.add_argument("--business-slug", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=False)
    parser.add_argument(
        "--role",
        required=True,
        choices=["boss", "manager", "staff"],
    )
    parser.add_argument("--password", required=False)
    parser.add_argument("--yes", action="store_true")

    return parser


def get_password(value: str | None) -> str:
    """Read password from argument or secure prompt."""

    if value is not None:
        return value

    password = getpass.getpass("Kullanıcı şifresi: ")
    password_repeat = getpass.getpass("Kullanıcı şifresi tekrar: ")

    if password != password_repeat:
        raise BusinessUserManagementError("Şifreler eşleşmiyor.")

    return password


def confirm_creation(username: str, role: str, business_slug: str, yes: bool) -> None:
    """Confirm user creation."""

    if yes:
        return

    print("")
    print("İşletme kullanıcısı oluşturulacak.")
    print(f"İşletme slug: {business_slug}")
    print(f"Kullanıcı adı: {username}")
    print(f"Rol: {role}")
    print("")
    confirmation = input("Devam etmek için EVET yazın: ").strip()

    if confirmation != "EVET":
        raise BusinessUserManagementError("İşlem iptal edildi.")


def main() -> None:
    """Create business user."""

    parser = build_parser()
    args = parser.parse_args()
    db = SessionLocal()

    try:
        current_user = get_user_by_username(
            db=db,
            username=args.super_admin_username,
            business_id=None,
        )

        if current_user is None:
            raise BusinessUserManagementError("Super admin kullanıcı bulunamadı.")

        business = get_business_by_slug(
            db=db,
            slug=args.business_slug,
        )

        if business is None:
            raise BusinessUserManagementError("İşletme bulunamadı.")

        password = get_password(args.password)

        confirm_creation(
            username=args.username,
            role=args.role,
            business_slug=args.business_slug,
            yes=args.yes,
        )

        user = create_business_user(
            db=db,
            current_user=current_user,
            business=business,
            full_name=args.full_name,
            username=args.username,
            password=password,
            role=args.role,
            email=args.email,
            ip_address="business-user-cli",
            user_agent="Missio create business user command",
        )
        db.commit()
        db.refresh(user)

        print("İşletme kullanıcısı başarıyla oluşturuldu.")
        print(f"Business ID: {user.business_id}")
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Role: {user.role}")
    except WeakPasswordError as exc:
        db.rollback()
        print("Şifre güvenlik politikasına uygun değil:")
        for error in exc.errors:
            print(f"- {error}")
        sys.exit(1)
    except DuplicateUsernameError as exc:
        db.rollback()
        print(f"Kullanıcı adı hatası: {exc}")
        sys.exit(1)
    except InvalidBusinessUserRoleError as exc:
        db.rollback()
        print(f"Rol hatası: {exc}")
        sys.exit(1)
    except RolePermissionError as exc:
        db.rollback()
        print(f"Yetki hatası: {exc}")
        sys.exit(1)
    except BusinessUserManagementError as exc:
        db.rollback()
        print(f"İşletme kullanıcısı oluşturma hatası: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
