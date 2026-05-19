from __future__ import annotations

import argparse
import getpass
import sys

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.services.bootstrap_service import (
    BootstrapAlreadyCompletedError,
    BootstrapError,
    BootstrapInconsistentStateError,
    create_initial_super_admin,
)
from app.services.auth_service import WeakPasswordError


def build_parser() -> argparse.ArgumentParser:
    """Build command argument parser."""

    parser = argparse.ArgumentParser(
        description="Create Missio initial super admin user.",
    )
    parser.add_argument("--full-name", required=False, help="Super admin full name.")
    parser.add_argument("--username", required=False, help="Super admin username.")
    parser.add_argument("--email", required=False, help="Super admin email.")
    parser.add_argument("--password", required=False, help="Super admin password.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm creation without interactive confirmation.",
    )

    return parser


def get_required_value(current_value: str | None, prompt: str) -> str:
    """Read required value from argument or prompt."""

    if current_value is not None and current_value.strip():
        return current_value.strip()

    value = input(prompt).strip()

    if not value:
        raise BootstrapError("Zorunlu alan boş bırakılamaz.")

    return value


def get_password(current_value: str | None) -> str:
    """Read password from argument or secure prompt."""

    if current_value is not None:
        return current_value

    password = getpass.getpass("Super admin şifresi: ")
    password_repeat = getpass.getpass("Super admin şifresi tekrar: ")

    if password != password_repeat:
        raise BootstrapError("Şifreler eşleşmiyor.")

    return password


def confirm_creation(username: str, full_name: str, yes: bool) -> None:
    """Confirm super admin creation."""

    if yes:
        return

    print("")
    print("İlk super_admin oluşturulacak.")
    print(f"Kullanıcı adı: {username}")
    print(f"Ad soyad: {full_name}")
    print("")
    confirmation = input("Devam etmek için EVET yazın: ").strip()

    if confirmation != "EVET":
        raise BootstrapError("İşlem iptal edildi.")


def main() -> None:
    """Create initial super admin user."""

    parser = build_parser()
    args = parser.parse_args()

    db = SessionLocal()

    try:
        full_name = get_required_value(args.full_name, "Super admin ad soyad: ")
        username = get_required_value(args.username, "Super admin kullanıcı adı: ")
        password = get_password(args.password)
        email = args.email.strip() if args.email else None

        confirm_creation(username=username, full_name=full_name, yes=args.yes)

        user = create_initial_super_admin(
            db=db,
            full_name=full_name,
            username=username,
            password=password,
            email=email,
            ip_address="bootstrap-cli",
            user_agent="Missio bootstrap command",
        )
        db.commit()
        db.refresh(user)

        print("İlk super_admin başarıyla oluşturuldu.")
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print("setup_completed: true")
    except WeakPasswordError as exc:
        db.rollback()
        print("Şifre güvenlik politikasına uygun değil:")
        for error in exc.errors:
            print(f"- {error}")
        sys.exit(1)
    except BootstrapAlreadyCompletedError as exc:
        db.rollback()
        print(f"İlk kurulum zaten kapalı: {exc}")
        sys.exit(1)
    except BootstrapInconsistentStateError as exc:
        db.rollback()
        print(f"Kurulum durumu tutarsız: {exc}")
        sys.exit(1)
    except BootstrapError as exc:
        db.rollback()
        print(f"Bootstrap hatası: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
