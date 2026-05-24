from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
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
from app.services.subscription_service import (
    BusinessSubscriptionExpiredError,
    BusinessSubscriptionInactiveError,
    BusinessSubscriptionNotFoundError,
    ensure_business_subscription_is_usable_for_login,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


SUBSCRIPTION_LOCK_BYPASS_PATHS = {
    "/api/v1/auth/me",
}


def ensure_current_user_subscription_allows_operation(
    *,
    current_user: User,
    request: Request,
    db: Session,
) -> None:
    """
    Block tenant operations when subscription is not usable.

    Expired tenants may still call /auth/me so the frontend can show a locked
    subscription screen, but operational endpoints must be blocked.
    """

    if current_user.business_id is None:
        return

    if request.url.path in SUBSCRIPTION_LOCK_BYPASS_PATHS:
        return

    try:
        ensure_business_subscription_is_usable_for_login(
            db=db,
            business_id=current_user.business_id,
        )
    except BusinessSubscriptionExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "SUBSCRIPTION_EXPIRED",
                "message": "Abonelik süresi dolduğu için bu işlem yapılamaz.",
            },
        ) from exc
    except BusinessSubscriptionInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "SUBSCRIPTION_LOCKED",
                "message": "Abonelik aktif olmadığı için bu işlem yapılamaz.",
            },
        ) from exc
    except BusinessSubscriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "SUBSCRIPTION_NOT_FOUND",
                "message": "İşletme aboneliği bulunamadığı için bu işlem yapılamaz.",
            },
        ) from exc


def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Return current authenticated user from bearer token."""

    try:
        current_user = get_authenticated_user_from_token(db=db, token=token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum doğrulanamadı.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    ensure_current_user_subscription_allows_operation(
        current_user=current_user,
        request=request,
        db=db,
    )

    return current_user


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
