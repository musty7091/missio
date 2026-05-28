from __future__ import annotations

from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.roles import UserRole
from app.core.security import hash_password
from app.db.session import get_db
from app.models.business import Business
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User
from app.services.audit_log_service import create_audit_log


router = APIRouter(
    prefix="/password-reset-requests",
    tags=["password-reset-requests"],
)


class PasswordResetRequestResponse(BaseModel):
    """Safe password reset request response for authorized users."""

    id: int
    business_id: int
    business_name: str | None
    requested_username: str
    target_user_id: int
    target_full_name: str
    target_role: str
    status: str
    requested_at_utc: datetime
    resolved_at_utc: datetime | None
    resolved_by_user_id: int | None



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


def get_utc_now_for_password_reset_route() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def generate_temporary_password() -> str:
    """Generate a temporary password compatible with the password policy."""

    number = secrets.randbelow(900000) + 100000
    return f"Missio.{number}!"


class PasswordResetRequestResetResponse(BaseModel):
    """Response returned after an authorized password reset."""

    request_id: int
    target_user_id: int
    target_username: str
    temporary_password: str
    must_change_password: bool
    message: str


def can_current_user_see_password_reset_request(
    current_user: User,
    target_user: User,
) -> bool:
    """Return whether current user can see the target user's password reset request."""

    if current_user.role == UserRole.SUPER_ADMIN.value:
        return target_user.role in {
            UserRole.SUPER_ADMIN.value,
            UserRole.BOSS.value,
        }

    if current_user.business_id is None:
        return False

    if target_user.business_id != current_user.business_id:
        return False

    if current_user.role == UserRole.BOSS.value:
        return target_user.role in {
            UserRole.MANAGER.value,
            UserRole.STAFF.value,
        }

    if current_user.role == UserRole.MANAGER.value:
        return target_user.role == UserRole.STAFF.value

    return False


def build_password_reset_request_response(
    reset_request: PasswordResetRequest,
    *,
    business: Business | None,
    target_user: User,
) -> PasswordResetRequestResponse:
    """Build safe password reset request response."""

    return PasswordResetRequestResponse(
        id=reset_request.id,
        business_id=reset_request.business_id,
        business_name=business.name if business is not None else None,
        requested_username=reset_request.requested_username,
        target_user_id=target_user.id,
        target_full_name=target_user.full_name,
        target_role=target_user.role,
        status=reset_request.status,
        requested_at_utc=reset_request.requested_at_utc,
        resolved_at_utc=reset_request.resolved_at_utc,
        resolved_by_user_id=reset_request.resolved_by_user_id,
    )


@router.get("", response_model=list[PasswordResetRequestResponse])
def list_password_reset_requests_endpoint(
    status_filter: str = "pending",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PasswordResetRequestResponse]:
    """List password reset requests visible to the current authorized user."""

    if current_user.role not in {
        UserRole.SUPER_ADMIN.value,
        UserRole.BOSS.value,
        UserRole.MANAGER.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        )

    normalized_status = status_filter.strip().lower()

    if normalized_status not in {"pending", "resolved", "rejected", "expired", "all"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Şifre talebi durum filtresi geçersiz.",
        )

    statement = (
        select(PasswordResetRequest, User, Business)
        .join(User, User.id == PasswordResetRequest.target_user_id)
        .join(Business, Business.id == PasswordResetRequest.business_id)
        .order_by(
            PasswordResetRequest.requested_at_utc.desc(),
            PasswordResetRequest.id.desc(),
        )
    )

    if normalized_status != "all":
        statement = statement.where(PasswordResetRequest.status == normalized_status)

    rows = db.execute(statement).all()

    response_items: list[PasswordResetRequestResponse] = []

    for reset_request, target_user, business in rows:
        if not can_current_user_see_password_reset_request(
            current_user=current_user,
            target_user=target_user,
        ):
            continue

        response_items.append(
            build_password_reset_request_response(
                reset_request,
                business=business,
                target_user=target_user,
            )
        )

    return response_items

@router.post("/{request_id}/reset", response_model=PasswordResetRequestResetResponse)
def reset_password_request_endpoint(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PasswordResetRequestResetResponse:
    """Reset a user's password from a visible pending password reset request."""

    reset_request = db.get(PasswordResetRequest, request_id)

    if reset_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="?ifre s?f?rlama talebi bulunamad?.",
        )

    if reset_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ?ifre s?f?rlama talebi art?k beklemede de?il.",
        )

    target_user = db.get(User, reset_request.target_user_id)

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talebe ba?l? kullan?c? bulunamad?.",
        )

    if not can_current_user_see_password_reset_request(
        current_user=current_user,
        target_user=target_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ?ifre s?f?rlama talebi i?in yetkiniz yok.",
        )

    temporary_password = generate_temporary_password()
    now = get_utc_now_for_password_reset_route()

    target_user.password_hash = hash_password(temporary_password)
    target_user.must_change_password = True
    target_user.updated_at = now

    reset_request.status = "resolved"
    reset_request.resolved_at_utc = now
    reset_request.resolved_by_user_id = current_user.id
    reset_request.resolution_note = "password_reset_completed"
    reset_request.updated_at_utc = now

    create_audit_log(
        db=db,
        action="auth.password_reset_completed",
        business_id=target_user.business_id,
        user_id=current_user.id,
        entity_type="user",
        entity_id=str(target_user.id),
        detail={
            "request_id": reset_request.id,
            "target_username": target_user.username,
            "target_role": target_user.role,
            "must_change_password": True,
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    db.add(target_user)
    db.add(reset_request)
    db.commit()
    db.refresh(target_user)
    db.refresh(reset_request)

    return PasswordResetRequestResetResponse(
        request_id=reset_request.id,
        target_user_id=target_user.id,
        target_username=target_user.username,
        temporary_password=temporary_password,
        must_change_password=target_user.must_change_password,
        message="Ge?ici ?ifre olu?turuldu. Kullan?c? ilk giri?te ?ifresini de?i?tirmelidir.",
    )

