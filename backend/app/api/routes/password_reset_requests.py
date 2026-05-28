from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.roles import UserRole
from app.db.session import get_db
from app.models.business import Business
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User


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