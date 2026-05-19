from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.business_repository import get_business_by_slug
from app.schemas.auth import LoginRequest, TokenResponse, UserMeResponse
from app.services.auth_service import (
    AccountTemporarilyLockedError,
    AuthServiceError,
    InactiveUserError,
    InvalidCredentialsError,
    authenticate_user,
    create_login_token_for_user,
    record_login_failure,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def get_client_ip(request: Request) -> str | None:
    """Return best-effort client IP address."""

    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()[:100]

    if request.client is None:
        return None

    return request.client.host[:100]


def get_user_agent(request: Request) -> str | None:
    """Return normalized user agent from request headers."""

    user_agent = request.headers.get("user-agent")

    if not user_agent:
        return None

    return user_agent.strip()[:1000]


def raise_safe_login_error() -> None:
    """Raise generic safe login error without leaking business or user existence."""

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kullanıcı adı veya şifre hatalı.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def resolve_login_business_id(
    db: Session,
    *,
    business_slug: str | None,
    username: str,
    ip_address: str | None,
    user_agent: str | None,
) -> int | None:
    """Resolve optional business slug to business_id for scoped login."""

    if business_slug is None:
        return None

    business = get_business_by_slug(db=db, slug=business_slug)

    if business is None:
        record_login_failure(
            db=db,
            username=username,
            business_id=None,
            user=None,
            failure_reason="invalid_business_slug",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise_safe_login_error()

    if not business.is_active:
        record_login_failure(
            db=db,
            username=username,
            business_id=business.id,
            user=None,
            failure_reason="inactive_business",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise_safe_login_error()

    return business.id


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return a bearer access token."""

    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    try:
        login_business_id = resolve_login_business_id(
            db=db,
            business_slug=payload.business_slug,
            username=payload.username,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        user = authenticate_user(
            db=db,
            username=payload.username,
            password=payload.password,
            business_id=login_business_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        login_token = create_login_token_for_user(user)
        db.commit()

        return TokenResponse(
            access_token=login_token.access_token,
            token_type=login_token.token_type,
            expires_in_minutes=login_token.expires_in_minutes,
        )
    except AccountTemporarilyLockedError as exc:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla hatalı giriş denemesi. Lütfen daha sonra tekrar deneyin.",
        ) from exc
    except (InvalidCredentialsError, InactiveUserError) as exc:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except AuthServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Giriş işlemi tamamlanamadı.",
        ) from exc
    except HTTPException:
        db.commit()
        raise
    except Exception:
        db.rollback()
        raise


@router.get("/me", response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user)) -> UserMeResponse:
    """Return safe current user profile for the authenticated session."""

    return UserMeResponse(
        id=current_user.id,
        business_id=current_user.business_id,
        full_name=current_user.full_name,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        theme_preference=current_user.theme_preference,
    )
