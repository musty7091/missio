from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.business import Business
from app.models.daily_operation_closure import DailyOperationClosure
from app.models.daily_operation_closure_item import DailyOperationClosureItem
from app.models.user import User
from app.schemas.daily_operation_closure import (
    CreateDailyOperationClosureRequest,
    DailyOperationClosureCreatedResponse,
    DailyOperationClosureItemResponse,
    DailyOperationClosureListResponse,
    DailyOperationClosureResponse,
)
from app.services.daily_operation_closure_service import (
    DailyOperationClosureAlreadyExistsError,
    DailyOperationClosureNotFoundError,
    DailyOperationClosureNotReadyError,
    DailyOperationClosurePermissionError,
    DailyOperationClosureServiceError,
    cleanup_old_daily_operation_closures,
    create_daily_operation_closure,
    get_daily_operation_closure_detail,
    list_daily_operation_closures,
)
from app.services.daily_operation_closure_pdf_service import build_daily_operation_closure_pdf_bytes
from app.core.roles import UserRole


router = APIRouter(prefix="/daily-closures", tags=["daily-closures"])


def map_daily_closure_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DailyOperationClosureNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, DailyOperationClosurePermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(exc, DailyOperationClosureAlreadyExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, DailyOperationClosureNotReadyError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, DailyOperationClosureServiceError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Gün kapanış işlemi tamamlanamadı.",
    )


def get_business_or_404(db: Session, *, business_id: int) -> Business:
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


def build_daily_operation_closure_item_response(
    item: DailyOperationClosureItem,
) -> DailyOperationClosureItemResponse:
    return DailyOperationClosureItemResponse(
        id=item.id,
        closure_id=item.closure_id,
        business_id=item.business_id,
        task_id=item.task_id,
        task_date=item.task_date,
        assigned_to_user_id=item.assigned_to_user_id,
        assigned_to_user_full_name=item.assigned_to_user_full_name,
        assigned_to_username=item.assigned_to_username,
        task_title=item.task_title,
        task_description=item.task_description,
        task_type=item.task_type,
        task_status=item.task_status,
        task_priority=item.task_priority,
        requires_photo=item.requires_photo,
        requires_location=item.requires_location,
        requires_manager_approval=item.requires_manager_approval,
        has_photo_evidence=item.has_photo_evidence,
        assigned_at_utc=item.assigned_at_utc,
        started_at_utc=item.started_at_utc,
        completed_at_utc=item.completed_at_utc,
        approved_at_utc=item.approved_at_utc,
        created_at_utc=item.created_at_utc,
    )


def build_daily_operation_closure_response(
    closure: DailyOperationClosure,
    *,
    items: list[DailyOperationClosureItem] | None = None,
) -> DailyOperationClosureResponse:
    return DailyOperationClosureResponse(
        id=closure.id,
        business_id=closure.business_id,
        closure_date=closure.closure_date,
        closed_by_user_id=closure.closed_by_user_id,
        closed_by_user_full_name=closure.closed_by_user_full_name,
        closed_by_username=closure.closed_by_username,
        closed_by_role=closure.closed_by_role,
        closed_at_utc=closure.closed_at_utc,
        status=closure.status,
        manager_note=closure.manager_note,
        total_task_count=closure.total_task_count,
        completed_task_count=closure.completed_task_count,
        approved_task_count=closure.approved_task_count,
        open_task_count=closure.open_task_count,
        rejected_task_count=closure.rejected_task_count,
        approval_pending_task_count=closure.approval_pending_task_count,
        photo_required_task_count=closure.photo_required_task_count,
        photo_evidence_task_count=closure.photo_evidence_task_count,
        created_at_utc=closure.created_at_utc,
        items=[
            build_daily_operation_closure_item_response(item)
            for item in (items or [])
        ],
    )


@router.post(
    "",
    response_model=DailyOperationClosureCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_daily_operation_closure_endpoint(
    payload: CreateDailyOperationClosureRequest,
    business_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyOperationClosureCreatedResponse:
    """Close a business operation day and create official report snapshot."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        cleanup_old_daily_operation_closures(
            db=db,
            business_id=business.id,
        )

        closure = create_daily_operation_closure(
            db=db,
            current_user=current_user,
            business=business,
            closure_date=payload.closure_date,
            manager_note=payload.manager_note,
        )

        db.commit()
        db.refresh(closure)

        closure, items = get_daily_operation_closure_detail(
            db=db,
            current_user=current_user,
            closure_id=closure.id,
        )

        message = (
            "Gün temiz kapanış olarak kapatıldı ve gün sonu raporu oluşturuldu."
            if closure.status == "closed_clean"
            else "Gün sorunlu kapanış olarak kapatıldı ve gün sonu raporu oluşturuldu."
        )

        return DailyOperationClosureCreatedResponse(
            closure=build_daily_operation_closure_response(closure, items=items),
            message=message,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_daily_closure_error(exc) from exc


@router.get(
    "",
    response_model=DailyOperationClosureListResponse,
)
def list_daily_operation_closures_endpoint(
    business_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyOperationClosureListResponse:
    """List official end-of-day operation closure reports."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        deleted_report_count = cleanup_old_daily_operation_closures(
            db=db,
            business_id=business.id,
        )

        if deleted_report_count > 0:
            db.commit()

        result = list_daily_operation_closures(
            db=db,
            current_user=current_user,
            business=business,
            limit=limit,
            offset=offset,
        )

        return DailyOperationClosureListResponse(
            closures=[
                build_daily_operation_closure_response(closure)
                for closure in result.closures
            ],
            total_count=result.total_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise map_daily_closure_error(exc) from exc


@router.get(
    "/{closure_id}/pdf",
)
def download_daily_operation_closure_pdf_endpoint(
    closure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download one official end-of-day closure report as a generated PDF."""

    try:
        closure, items = get_daily_operation_closure_detail(
            db=db,
            current_user=current_user,
            closure_id=closure_id,
        )

        business = get_business_or_404(db=db, business_id=closure.business_id)

        pdf_bytes = build_daily_operation_closure_pdf_bytes(
            closure=closure,
            items=items,
            business=business,
        )

        filename = f"missio-gun-sonu-raporu-{closure.closure_date.isoformat()}.pdf"

        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise map_daily_closure_error(exc) from exc


@router.get(
    "/{closure_id}",
    response_model=DailyOperationClosureResponse,
)
def get_daily_operation_closure_detail_endpoint(
    closure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyOperationClosureResponse:
    """Return one official end-of-day operation closure report with task rows."""

    try:
        closure, items = get_daily_operation_closure_detail(
            db=db,
            current_user=current_user,
            closure_id=closure_id,
        )

        return build_daily_operation_closure_response(closure, items=items)
    except HTTPException:
        raise
    except Exception as exc:
        raise map_daily_closure_error(exc) from exc
