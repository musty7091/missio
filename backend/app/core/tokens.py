from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings
from app.core.roles import is_valid_role


ALGORITHM = "HS256"
TOKEN_TYPE_ACCESS = "access"
TOKEN_ISSUER = "missio"


class InvalidTokenError(ValueError):
    """Raised when a JWT token is invalid or expired."""


@dataclass(frozen=True)
class AccessTokenPayload:
    """Validated access token payload."""

    subject: str
    role: str
    business_id: int | None
    expires_at: datetime
    issued_at: datetime


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def create_access_token(
    subject: str,
    role: str,
    business_id: int | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""

    if not subject:
        raise ValueError("Token subject boş olamaz.")

    if not is_valid_role(role):
        raise ValueError("Geçersiz kullanıcı rolü.")

    now = get_utc_now()

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expires_at = now + expires_delta

    claims: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "business_id": business_id,
        "type": TOKEN_TYPE_ACCESS,
        "iss": TOKEN_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    return jwt.encode(
        claims,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> AccessTokenPayload:
    """Decode and validate a signed JWT access token."""

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            issuer=TOKEN_ISSUER,
        )
    except JWTError as exc:
        raise InvalidTokenError("Token geçersiz veya süresi dolmuş.") from exc

    subject = payload.get("sub")
    role = payload.get("role")
    token_type = payload.get("type")
    business_id = payload.get("business_id")
    issued_at_timestamp = payload.get("iat")
    expires_at_timestamp = payload.get("exp")

    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("Token subject bilgisi geçersiz.")

    if not isinstance(role, str) or not is_valid_role(role):
        raise InvalidTokenError("Token rol bilgisi geçersiz.")

    if token_type != TOKEN_TYPE_ACCESS:
        raise InvalidTokenError("Token tipi geçersiz.")

    if business_id is not None and not isinstance(business_id, int):
        raise InvalidTokenError("Token işletme bilgisi geçersiz.")

    if not isinstance(issued_at_timestamp, int):
        raise InvalidTokenError("Token oluşturma zamanı geçersiz.")

    if not isinstance(expires_at_timestamp, int):
        raise InvalidTokenError("Token son kullanma zamanı geçersiz.")

    return AccessTokenPayload(
        subject=subject,
        role=role,
        business_id=business_id,
        issued_at=datetime.fromtimestamp(
            issued_at_timestamp,
            tz=timezone.utc,
        ),
        expires_at=datetime.fromtimestamp(
            expires_at_timestamp,
            tz=timezone.utc,
        ),
    )
