from __future__ import annotations

from datetime import timedelta

from app.core.tokens import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)


def check_valid_access_token() -> None:
    """Create and decode a valid token."""

    token = create_access_token(
        subject="1",
        role="super_admin",
        business_id=None,
        expires_delta=timedelta(minutes=15),
    )

    payload = decode_access_token(token)

    if payload.subject != "1":
        raise RuntimeError("Token subject hatalı.")

    if payload.role != "super_admin":
        raise RuntimeError("Token rol bilgisi hatalı.")

    if payload.business_id is not None:
        raise RuntimeError("Token business_id bilgisi hatalı.")

    print("Geçerli access token kontrolü başarılı.")


def check_business_access_token() -> None:
    """Create and decode a business scoped token."""

    token = create_access_token(
        subject="10",
        role="staff",
        business_id=1,
        expires_delta=timedelta(minutes=15),
    )

    payload = decode_access_token(token)

    if payload.subject != "10":
        raise RuntimeError("Personel token subject hatalı.")

    if payload.role != "staff":
        raise RuntimeError("Personel token rol bilgisi hatalı.")

    if payload.business_id != 1:
        raise RuntimeError("Personel token business_id bilgisi hatalı.")

    print("İşletme kapsamlı access token kontrolü başarılı.")


def check_invalid_role_rejected() -> None:
    """Invalid roles must not produce tokens."""

    try:
        create_access_token(
            subject="1",
            role="invalid_role",
            business_id=None,
            expires_delta=timedelta(minutes=15),
        )
    except ValueError:
        print("Geçersiz rol reddetme kontrolü başarılı.")
        return

    raise RuntimeError("Geçersiz rol ile token üretildi.")


def check_expired_token_rejected() -> None:
    """Expired tokens must be rejected."""

    token = create_access_token(
        subject="1",
        role="super_admin",
        business_id=None,
        expires_delta=timedelta(seconds=-1),
    )

    try:
        decode_access_token(token)
    except InvalidTokenError:
        print("Süresi dolmuş token reddetme kontrolü başarılı.")
        return

    raise RuntimeError("Süresi dolmuş token kabul edildi.")


def main() -> None:
    """Run all JWT token checks."""

    check_valid_access_token()
    check_business_access_token()
    check_invalid_role_rejected()
    check_expired_token_rejected()
    print("Token güvenlik temel kontrolü başarılı.")


if __name__ == "__main__":
    main()
