from datetime import timedelta

import pytest

from app.core.tokens import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_super_admin_access_token() -> None:
    token = create_access_token(
        subject="1",
        role="super_admin",
        business_id=None,
        expires_delta=timedelta(minutes=15),
    )

    payload = decode_access_token(token)

    assert payload.subject == "1"
    assert payload.role == "super_admin"
    assert payload.business_id is None


def test_create_and_decode_staff_access_token() -> None:
    token = create_access_token(
        subject="15",
        role="staff",
        business_id=2,
        expires_delta=timedelta(minutes=15),
    )

    payload = decode_access_token(token)

    assert payload.subject == "15"
    assert payload.role == "staff"
    assert payload.business_id == 2


def test_create_access_token_rejects_invalid_role() -> None:
    with pytest.raises(ValueError):
        create_access_token(
            subject="1",
            role="invalid_role",
            business_id=None,
            expires_delta=timedelta(minutes=15),
        )


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        subject="1",
        role="super_admin",
        business_id=None,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_decode_access_token_rejects_invalid_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-valid-token")
