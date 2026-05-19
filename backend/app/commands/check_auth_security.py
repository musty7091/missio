from __future__ import annotations

from app.core.roles import (
    can_manage_operations,
    get_all_role_values,
    get_role_label,
    is_admin_role,
)
from app.core.security import (
    hash_password,
    is_password_strong,
    validate_password_strength,
    verify_password,
)


def check_password_hashing() -> None:
    """Validate password hashing and verification helpers."""

    sample_password = "Missio.2026!"
    wrong_password = "Wrong.2026!"
    password_hash = hash_password(sample_password)

    if sample_password in password_hash:
        raise RuntimeError("Hash içinde açık şifre görünüyor.")

    if not verify_password(sample_password, password_hash):
        raise RuntimeError("Doğru şifre doğrulanamadı.")

    if verify_password(wrong_password, password_hash):
        raise RuntimeError("Yanlış şifre hatalı şekilde doğrulandı.")

    print("Parola hash kontrolü başarılı.")


def check_password_policy() -> None:
    """Validate password policy helper."""

    weak_password = "123"
    strong_password = "Missio.2026!"

    weak_errors = validate_password_strength(weak_password)

    if not weak_errors:
        raise RuntimeError("Zayıf şifre hatalı şekilde güçlü kabul edildi.")

    if not is_password_strong(strong_password):
        raise RuntimeError("Güçlü şifre hatalı şekilde reddedildi.")

    print("Parola politika kontrolü başarılı.")
    print("Zayıf şifre hata sayısı:", len(weak_errors))


def check_roles() -> None:
    """Validate role definitions."""

    role_values = get_all_role_values()

    if "super_admin" not in role_values:
        raise RuntimeError("super_admin rolü eksik.")

    if "staff" not in role_values:
        raise RuntimeError("staff rolü eksik.")

    if not is_admin_role("super_admin"):
        raise RuntimeError("super_admin admin rolü olarak tanınmadı.")

    if is_admin_role("staff"):
        raise RuntimeError("staff hatalı şekilde admin rolü kabul edildi.")

    if not can_manage_operations("manager"):
        raise RuntimeError("manager operasyon yönetebilir olmalı.")

    print("Rol kontrolü başarılı.")
    print("Tanımlı roller:")
    for role in role_values:
        print(f"- {role}: {get_role_label(role)}")


def main() -> None:
    """Run all auth security checks."""

    check_password_hashing()
    check_password_policy()
    check_roles()
    print("Auth güvenlik temel kontrolü başarılı.")


if __name__ == "__main__":
    main()
