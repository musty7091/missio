from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.access_control_service import (
    AccessControlError,
    ensure_business_scope,
    require_roles,
)
from app.services.session_user_service import (
    AuthenticationError,
    get_authenticated_user_from_token,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Return current authenticated user from bearer token."""

    try:
        return get_authenticated_user_from_token(db=db, token=token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum doğrulanamadı.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_roles_dependency(*allowed_roles: str) -> Callable[[User], User]:
    """Create FastAPI dependency for role based access control."""

    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        try:
            require_roles(current_user, allowed_roles)
        except AccessControlError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz yok.",
            ) from exc

        return current_user

    return dependency


def require_business_scope_dependency(
    target_business_id: int,
) -> Callable[[User], User]:
    """Create FastAPI dependency for business scope access control."""

    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        try:
            ensure_business_scope(current_user, target_business_id)
        except AccessControlError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işletme verisine erişim yetkiniz yok.",
            ) from exc

        return current_user

    return dependency
