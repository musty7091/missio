from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.tokens import InvalidTokenError, decode_access_token
from app.models.user import User
from app.repositories.user_repository import get_user_by_id


class AuthenticationError(ValueError):
    """Raised when authentication cannot be completed safely."""


class AuthenticatedUserMismatchError(AuthenticationError):
    """Raised when token and database user data do not match."""


def parse_token_subject_as_user_id(subject: str) -> int:
    """Parse JWT subject as integer user id."""

    try:
        user_id = int(subject)
    except ValueError as exc:
        raise AuthenticationError("Token kullanıcı bilgisi geçersiz.") from exc

    if user_id <= 0:
        raise AuthenticationError("Token kullanıcı bilgisi geçersiz.")

    return user_id


def get_authenticated_user_from_token(db: Session, token: str) -> User:
    """Return active database user represented by a valid access token."""

    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise AuthenticationError("Oturum doğrulanamadı.") from exc

    user_id = parse_token_subject_as_user_id(payload.subject)
    user = get_user_by_id(db=db, user_id=user_id)

    if user is None:
        raise AuthenticationError("Kullanıcı bulunamadı.")

    if not user.is_active:
        raise AuthenticationError("Kullanıcı pasif durumda.")

    if user.role != payload.role:
        raise AuthenticatedUserMismatchError("Token rol bilgisi kullanıcıyla eşleşmiyor.")

    if user.business_id != payload.business_id:
        raise AuthenticatedUserMismatchError(
            "Token işletme bilgisi kullanıcıyla eşleşmiyor.",
        )

    return user
