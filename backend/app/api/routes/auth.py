from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import hash_password, validate_password_strength, verify_password
from app.db.session import get_db
from app.models.user import User
from app.models.password_reset_request import PasswordResetRequest
from app.repositories.business_repository import get_business_by_slug
from app.repositories.user_repository import normalize_email, normalize_username
from app.schemas.auth import LoginRequest, TokenResponse, UserMeResponse
from app.services.audit_log_service import create_audit_log
from app.services.subscription_service import get_current_business_subscription
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




class ForgotPasswordRequest(BaseModel):
    """Request payload for public forgot-password request."""

    business_slug: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=1, max_length=100)


class ForgotPasswordResponse(BaseModel):
    """Safe response returned after forgot-password request."""

    message: str

class UpdateMyProfileRequest(BaseModel):
    """Request payload for updating the authenticated user's own profile."""

    full_name: str = Field(min_length=1, max_length=150)
    email: str | None = Field(default=None, max_length=255)


class UpdateMyProfileResponse(BaseModel):
    """Response returned after updating the authenticated user's own profile."""

    user: UserMeResponse
    message: str


class ChangeOwnPasswordRequest(BaseModel):
    """Request payload for changing the authenticated user's own password."""

    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=1, max_length=255)
    new_password_repeat: str = Field(min_length=1, max_length=255)


class ChangeOwnPasswordResponse(BaseModel):
    """Response returned after changing the authenticated user's own password."""

    message: str



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


def create_safe_forgot_password_response() -> ForgotPasswordResponse:
    """Return generic forgot-password response without leaking user existence."""

    return ForgotPasswordResponse(
        message=(
            "Talebin yetkili kişiye iletildi. "
            "Şifren sıfırlandığında işletme yetkilinden bilgi alabilirsin."
        ),
    )


def create_password_reset_request_if_user_exists(
    db: Session,
    *,
    business_slug: str,
    username: str,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    """Create pending password reset request only if business and user exist."""

    normalized_username = normalize_username(username)
    normalized_business_slug = business_slug.strip().lower()

    if not normalized_business_slug or not normalized_username:
        return

    business = get_business_by_slug(db=db, slug=normalized_business_slug)

    if business is None or not business.is_active:
        return

    user = (
        db.query(User)
        .filter(
            User.business_id == business.id,
            User.username == normalized_username,
            User.is_active.is_(True),
        )
        .one_or_none()
    )

    if user is None:
        return

    now = get_utc_now_for_auth_route()

    existing_pending_request = (
        db.query(PasswordResetRequest)
        .filter(
            PasswordResetRequest.business_id == business.id,
            PasswordResetRequest.target_user_id == user.id,
            PasswordResetRequest.status == "pending",
        )
        .order_by(PasswordResetRequest.id.desc())
        .first()
    )

    if existing_pending_request is not None:
        existing_pending_request.requested_at_utc = now
        existing_pending_request.updated_at_utc = now
        existing_pending_request.ip_address = ip_address
        existing_pending_request.user_agent = user_agent
        db.add(existing_pending_request)
        return

    reset_request = PasswordResetRequest(
        business_id=business.id,
        target_user_id=user.id,
        requested_username=normalized_username,
        status="pending",
        notification_status="not_attempted",
        notification_attempted_count=0,
        notification_sent_count=0,
        notification_failed_count=0,
        last_notification_attempt_at_utc=None,
        requested_at_utc=now,
        resolved_at_utc=None,
        resolved_by_user_id=None,
        resolution_note=None,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at_utc=now,
        updated_at_utc=now,
    )

    db.add(reset_request)

    create_audit_log(
        db=db,
        action="auth.password_reset_requested",
        business_id=business.id,
        user_id=user.id,
        entity_type="password_reset_request",
        entity_id=None,
        detail={
            "username": normalized_username,
            "business_slug": normalized_business_slug,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

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


def get_utc_now_for_auth_route() -> datetime:
    """Return current UTC datetime for auth route calculations."""

    return datetime.now(timezone.utc)


def as_utc_aware_for_auth_route(value: datetime | None) -> datetime | None:
    """Normalize datetime value for auth route comparisons."""

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def calculate_subscription_remaining_days_for_auth(value: datetime | None) -> int | None:
    """Calculate remaining whole days for auth/me response."""

    normalized_value = as_utc_aware_for_auth_route(value)

    if normalized_value is None:
        return None

    now = get_utc_now_for_auth_route()
    seconds = (normalized_value - now).total_seconds()

    if seconds < 0:
        return 0

    return int((seconds + 86_399) // 86_400)


def build_subscription_access_info(
    db: Session,
    *,
    current_user: User,
) -> dict[str, object]:
    """Build subscription access info for frontend routing."""

    if current_user.business_id is None:
        return {
            "subscription_access_status": "active",
            "subscription_status": None,
            "subscription_ends_at_utc": None,
            "subscription_remaining_days": None,
            "subscription_is_expired": False,
            "subscription_lock_reason": None,
        }

    subscription = get_current_business_subscription(
        db=db,
        business_id=current_user.business_id,
    )

    if subscription is None:
        return {
            "subscription_access_status": "locked",
            "subscription_status": None,
            "subscription_ends_at_utc": None,
            "subscription_remaining_days": None,
            "subscription_is_expired": False,
            "subscription_lock_reason": "missing_subscription",
        }

    ends_at_utc = as_utc_aware_for_auth_route(subscription.ends_at_utc)
    now = get_utc_now_for_auth_route()
    is_expired = ends_at_utc is not None and ends_at_utc < now

    if is_expired:
        access_status = "expired_locked"
        lock_reason = "subscription_expired"
    elif subscription.status not in {"trialing", "active"}:
        access_status = "locked"
        lock_reason = f"subscription_{subscription.status}"
    else:
        access_status = "active"
        lock_reason = None

    return {
        "subscription_access_status": access_status,
        "subscription_status": subscription.status,
        "subscription_ends_at_utc": subscription.ends_at_utc,
        "subscription_remaining_days": calculate_subscription_remaining_days_for_auth(
            subscription.ends_at_utc,
        ),
        "subscription_is_expired": is_expired,
        "subscription_lock_reason": lock_reason,
    }


@router.post("/forgot-password/request", response_model=ForgotPasswordResponse)
def forgot_password_request(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    """Create a safe public password reset request."""

    try:
        create_password_reset_request_if_user_exists(
            db=db,
            business_slug=payload.business_slug,
            username=payload.username,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        db.commit()
    except Exception:
        db.rollback()

    return create_safe_forgot_password_response()

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
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserMeResponse:
    """Return safe current user profile for the authenticated session."""

    subscription_access_info = build_subscription_access_info(
        db=db,
        current_user=current_user,
    )

    return UserMeResponse(
        id=current_user.id,
        business_id=current_user.business_id,
        full_name=current_user.full_name,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        theme_preference=current_user.theme_preference,
        must_change_password=current_user.must_change_password,
        **subscription_access_info,
    )

@router.post("/me/password", response_model=ChangeOwnPasswordResponse)
def change_my_password(
    payload: ChangeOwnPasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeOwnPasswordResponse:
    """Change the authenticated user's own password after current password verification."""

    try:
        if payload.new_password != payload.new_password_repeat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Yeni şifre ve yeni şifre tekrarı eşleşmiyor.",
            )

        if not verify_password(payload.current_password, current_user.password_hash):
            create_audit_log(
                db=db,
                action="auth.password_change_failed",
                business_id=current_user.business_id,
                user_id=current_user.id,
                entity_type="user",
                entity_id=str(current_user.id),
                detail={
                    "username": current_user.username,
                    "reason": "invalid_current_password",
                },
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
            )
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mevcut şifre hatalı.",
            )

        if verify_password(payload.new_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Yeni şifre mevcut şifre ile aynı olamaz.",
            )

        password_errors = validate_password_strength(payload.new_password)

        if password_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Yeni şifre güvenlik politikasına uygun değil.",
                    "errors": password_errors,
                },
            )

        current_user.password_hash = hash_password(payload.new_password)
        current_user.must_change_password = False
        current_user.updated_at = get_utc_now_for_auth_route()

        create_audit_log(
            db=db,
            action="auth.password_changed",
            business_id=current_user.business_id,
            user_id=current_user.id,
            entity_type="user",
            entity_id=str(current_user.id),
            detail={
                "username": current_user.username,
                "role": current_user.role,
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.add(current_user)
        db.commit()

        return ChangeOwnPasswordResponse(
            message="Şifreniz başarıyla değiştirildi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

@router.patch("/me/profile", response_model=UpdateMyProfileResponse)
def update_my_profile(
    payload: UpdateMyProfileRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UpdateMyProfileResponse:
    """Update the authenticated user's own profile information."""

    try:
        normalized_full_name = payload.full_name.strip()
        normalized_email = normalize_email(payload.email)

        if not normalized_full_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ad soyad boş olamaz.",
            )

        if normalized_email is not None:
            email_domain = normalized_email.split("@")[-1] if "@" in normalized_email else ""

            if "@" not in normalized_email or "." not in email_domain:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Geçerli bir e-posta adresi giriniz.",
                )

        changed_fields: list[str] = []

        if current_user.full_name != normalized_full_name:
            current_user.full_name = normalized_full_name
            changed_fields.append("full_name")

        if current_user.email != normalized_email:
            current_user.email = normalized_email
            changed_fields.append("email")

        current_user.updated_at = get_utc_now_for_auth_route()

        create_audit_log(
            db=db,
            action="auth.profile_updated",
            business_id=current_user.business_id,
            user_id=current_user.id,
            entity_type="user",
            entity_id=str(current_user.id),
            detail={
                "username": current_user.username,
                "changed_fields": changed_fields,
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        subscription_access_info = build_subscription_access_info(
            db=db,
            current_user=current_user,
        )

        return UpdateMyProfileResponse(
            user=UserMeResponse(
                id=current_user.id,
                business_id=current_user.business_id,
                full_name=current_user.full_name,
                username=current_user.username,
                email=current_user.email,
                role=current_user.role,
                is_active=current_user.is_active,
                theme_preference=current_user.theme_preference,
                **subscription_access_info,
            ),
            message="Profil bilgileriniz başarıyla güncellendi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

