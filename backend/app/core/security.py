from __future__ import annotations

import re
from dataclasses import dataclass

from passlib.context import CryptContext


password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


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
    """Hash a plain password using the configured password context."""

    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a stored password hash."""

    return password_context.verify(plain_password, password_hash)


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
