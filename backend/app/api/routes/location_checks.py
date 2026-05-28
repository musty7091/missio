from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.roles import UserRole
from app.db.session import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.location_check import (
    ALLOWED_LOCATION_CHECK_STATUSES,
    CreateLocationCheckRequest,
    FailLocationCheckRequest,
    LocationCheckCreatedResponse,
    LocationCheckListResponse,
    LocationCheckResponse,
    LocationCheckUpdatedResponse,
    ShareLocationCheckRequest,
)
from app.services.location_check_service import (
    InvalidLocationCheckStateError,
    InvalidLocationCheckTargetError,
    LocationCheckNotFoundError,
    LocationCheckPermissionError,
    LocationCheckServiceError,
    build_location_check_response,
    build_location_check_responses,
    create_location_checks,
    fail_location_check,
    list_location_checks_for_business,
    list_pending_location_checks_for_staff,
    mark_location_check_seen,
    send_location_check_notifications_safely,
    share_location_check,
)


router = APIRouter(prefix="/location-checks", tags=["location-checks"])

logger = logging.getLogger(__name__)


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


def get_business_or_404(db: Session, *, business_id: int) -> Business:
    """Return business by id or raise 404."""

    business = db.get(Business, business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı.",
        )

    return business


def resolve_business_for_current_user(
    db: Session,
    *,
    current_user: User,
    business_id: int | None = None,
) -> Business:
    """Resolve business scope for current user."""

    if current_user.role == UserRole.SUPER_ADMIN.value:
        if business_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super admin işlemleri için business_id gereklidir.",
            )

        return get_business_or_404(db=db, business_id=business_id)

    if current_user.business_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcının işletme kapsamı yok.",
        )

    if business_id is not None and business_id != current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işletme verisine erişim yetkiniz yok.",
        )

    return get_business_or_404(db=db, business_id=current_user.business_id)


def map_location_check_error(exc: Exception) -> HTTPException:
    """Map location check service errors to HTTP errors."""

    if isinstance(exc, LocationCheckNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, LocationCheckPermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(exc, InvalidLocationCheckStateError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        (
            InvalidLocationCheckTargetError,
            LocationCheckServiceError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Konum yoklama işlemi tamamlanamadı.",
    )


def commit_location_check_notification_side_effects_safely(
    db: Session,
    *,
    context: str,
) -> None:
    """Persist best-effort notification updates without blocking main workflow."""

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning(
            "MISSIO_LOCATION_CHECK_NOTIFICATION_COMMIT_FAILED context=%s error=%s",
            context,
            exc,
        )


@router.post(
    "",
    response_model=LocationCheckCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_location_check_endpoint(
    payload: CreateLocationCheckRequest,
    request: Request,
    business_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationCheckCreatedResponse:
    """Create one or many manual location check requests."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        if payload.target_user_id is not None:
            target_user_ids = [payload.target_user_id]
        else:
            target_user_ids = payload.target_user_ids or []

        checks = create_location_checks(
            db=db,
            current_user=current_user,
            business_id=business.id,
            target_user_ids=target_user_ids,
            request_note=payload.request_note,
        )

        db.commit()

        for check in checks:
            db.refresh(check)

        send_location_check_notifications_safely(
            db=db,
            checks=checks,
        )

        commit_location_check_notification_side_effects_safely(
            db=db,
            context="location_check_created_notification",
        )

        for check in checks:
            db.refresh(check)

        return LocationCheckCreatedResponse(
            checks=build_location_check_responses(checks, db=db),
            created_count=len(checks),
            message="Konum yoklama isteği oluşturuldu.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_location_check_error(exc) from exc


@router.get(
    "",
    response_model=LocationCheckListResponse,
)
def list_location_checks_endpoint(
    business_id: int | None = Query(default=None, gt=0),
    status_filter: str | None = Query(default=None, alias="status"),
    target_user_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationCheckListResponse:
    """List manual location checks for boss/manager screen."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        if status_filter is not None and status_filter not in ALLOWED_LOCATION_CHECK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Geçersiz konum yoklama durumu.",
            )

        result = list_location_checks_for_business(
            db=db,
            current_user=current_user,
            business_id=business.id,
            status=status_filter,
            target_user_id=target_user_id,
            limit=limit,
            offset=offset,
        )

        return LocationCheckListResponse(
            checks=build_location_check_responses(result.checks, db=db),
            total_count=result.total_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise map_location_check_error(exc) from exc


@router.get(
    "/my-pending",
    response_model=LocationCheckListResponse,
)
def list_my_pending_location_checks_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationCheckListResponse:
    """List current staff user's pending location check requests."""

    try:
        result = list_pending_location_checks_for_staff(
            db=db,
            current_user=current_user,
        )

        return LocationCheckListResponse(
            checks=build_location_check_responses(result.checks, db=db),
            total_count=result.total_count,
        )
    except Exception as exc:
        raise map_location_check_error(exc) from exc


@router.post(
    "/{location_check_id}/seen",
    response_model=LocationCheckUpdatedResponse,
)
def mark_location_check_seen_endpoint(
    location_check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationCheckUpdatedResponse:
    """Mark a location check request as seen by the target staff user."""

    try:
        check = mark_location_check_seen(
            db=db,
            current_user=current_user,
            location_check_id=location_check_id,
        )

        db.commit()
        db.refresh(check)

        return LocationCheckUpdatedResponse(
            check=build_location_check_response(check, db=db),
            message="Konum yoklama isteği görüldü olarak işaretlendi.",
        )
    except Exception as exc:
        db.rollback()
        raise map_location_check_error(exc) from exc


@router.post(
    "/{location_check_id}/share",
    response_model=LocationCheckUpdatedResponse,
)
def share_location_check_endpoint(
    location_check_id: int,
    payload: ShareLocationCheckRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationCheckUpdatedResponse:
    """Share current staff user's location for a location check request."""

    try:
        check = share_location_check(
            db=db,
            current_user=current_user,
            location_check_id=location_check_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_accuracy=payload.location_accuracy,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(check)

        return LocationCheckUpdatedResponse(
            check=build_location_check_response(check, db=db),
            message="Konum başarıyla paylaşıldı.",
        )
    except Exception as exc:
        db.rollback()
        raise map_location_check_error(exc) from exc


@router.post(
    "/{location_check_id}/fail",
    response_model=LocationCheckUpdatedResponse,
)
def fail_location_check_endpoint(
    location_check_id: int,
    payload: FailLocationCheckRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationCheckUpdatedResponse:
    """Store current staff user's failed location response."""

    try:
        check = fail_location_check(
            db=db,
            current_user=current_user,
            location_check_id=location_check_id,
            response_error_code=payload.response_error_code,
            response_error_message=payload.response_error_message,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(check)

        return LocationCheckUpdatedResponse(
            check=build_location_check_response(check, db=db),
            message="Konum yoklama hata durumu kaydedildi.",
        )
    except Exception as exc:
        db.rollback()
        raise map_location_check_error(exc) from exc
