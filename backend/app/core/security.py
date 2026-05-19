from __future__ import annotations

import re

import bcrypt
from dataclasses import dataclass


@dataclass(frozen=True)
class PasswordPolicy:
    """Password policy used across Missio authentication flows."""

    min_length: int = 10
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True


DEFAULT_PASSWORD_POLICY = PasswordPolicy()


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt directly."""

    if not isinstance(password, str):
        raise TypeError("Şifre metin formatında olmalıdır.")

    password_bytes = password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))

    return password_hash.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a stored bcrypt password hash."""

    if not plain_password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False


def validate_password_strength(
    password: str,
    policy: PasswordPolicy = DEFAULT_PASSWORD_POLICY,
) -> list[str]:
    """Return password validation errors. Empty list means password is valid."""

    errors: list[str] = []

    if len(password) < policy.min_length:
        errors.append(f"Şifre en az {policy.min_length} karakter olmalıdır.")

    if policy.require_uppercase and not re.search(r"[A-ZÇĞİÖŞÜ]", password):
        errors.append("Şifre en az bir büyük harf içermelidir.")

    if policy.require_lowercase and not re.search(r"[a-zçğıöşü]", password):
        errors.append("Şifre en az bir küçük harf içermelidir.")

    if policy.require_digit and not re.search(r"\d", password):
        errors.append("Şifre en az bir rakam içermelidir.")

    if policy.require_special and not re.search(r"[^A-Za-z0-9ÇĞİÖŞÜçğıöşü]", password):
        errors.append("Şifre en az bir özel karakter içermelidir.")

    return errors


def is_password_strong(password: str) -> bool:
    """Return whether a password satisfies the default password policy."""

    return not validate_password_strength(password)
