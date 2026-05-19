from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMeResponse
from app.services.auth_service import (
    AccountTemporarilyLockedError,
    AuthServiceError,
    InactiveUserError,
    InvalidCredentialsError,
    authenticate_user,
    create_login_token_for_user,
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


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return a bearer access token."""

    try:
        user = authenticate_user(
            db=db,
            username=payload.username,
            password=payload.password,
            business_id=None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
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
