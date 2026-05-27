from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.business import Business
from app.models.daily_operation_closure import DailyOperationClosure
from app.models.daily_operation_closure_item import DailyOperationClosureItem
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.models.user import User
from app.schemas.task import (
    TASK_ATTACHMENT_TYPE_EVIDENCE,
    TASK_STATUS_APPROVED,
    TASK_STATUS_ASSIGNED,
    TASK_STATUS_CANCELLED,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_REJECTED,
)
from app.services.access_control_service import ensure_business_scope


class DailyOperationClosureServiceError(ValueError):
    """Base error for daily operation closure failures."""


class DailyOperationClosurePermissionError(DailyOperationClosureServiceError):
    """Raised when user has no closure permission."""


class DailyOperationClosureNotFoundError(DailyOperationClosureServiceError):
    """Raised when closure report is not found."""


class DailyOperationClosureAlreadyExistsError(DailyOperationClosureServiceError):
    """Raised when a date is already closed."""


class DailyOperationClosureNotReadyError(DailyOperationClosureServiceError):
    """Raised when day cannot be closed because there are no tasks."""


class DailyOperationClosureNoteRequiredError(DailyOperationClosureServiceError):
    """Raised when problematic closure has no manager note."""


@dataclass(frozen=True)
class DailyOperationClosureListResult:
    closures: list[DailyOperationClosure]
    total_count: int


@dataclass(frozen=True)
class AutomaticDailyClosureBusinessResult:
    business_id: int
    business_name: str
    closure_date: date | None
    status: str
    message: str
    closure_id: int | None = None


@dataclass(frozen=True)
class AutomaticDailyClosureRunResult:
    checked_count: int
    closed_count: int
    skipped_count: int
    failed_count: int
    results: list[AutomaticDailyClosureBusinessResult]


DAILY_OPERATION_CLOSURE_STATUS_CLEAN = "closed_clean"
DAILY_OPERATION_CLOSURE_STATUS_WITH_ISSUES = "closed_with_issues"
DAILY_OPERATION_CLOSURE_STATUS_LEGACY_CLOSED = "closed"

DAILY_OPERATION_CLOSURE_FINAL_STATUSES = {
    DAILY_OPERATION_CLOSURE_STATUS_CLEAN,
    DAILY_OPERATION_CLOSURE_STATUS_WITH_ISSUES,
    DAILY_OPERATION_CLOSURE_STATUS_LEGACY_CLOSED,
}

DAILY_OPERATION_CLOSURE_RETENTION_DAYS = 60

DAILY_OPERATION_CLOSURE_CREATORS = {
    UserRole.MANAGER.value,
    UserRole.BOSS.value,
}

DAILY_OPERATION_CLOSURE_VIEWERS = {
    UserRole.MANAGER.value,
    UserRole.BOSS.value,
    UserRole.SUPER_ADMIN.value,
}

OPEN_OR_PROBLEM_STATUSES = {
    TASK_STATUS_ASSIGNED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_REJECTED,
}


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_daily_operation_closure_retention_cutoff_date(
    current_date: date | None = None,
) -> date:
    """Return the oldest closure date that is allowed to stay visible."""

    source_date = current_date or get_utc_now().date()

    return source_date - timedelta(days=DAILY_OPERATION_CLOSURE_RETENTION_DAYS)


def is_daily_operation_closure_expired(
    closure_date: date,
    *,
    current_date: date | None = None,
) -> bool:
    """Return whether the closure is older than the retention policy."""

    retention_cutoff_date = get_daily_operation_closure_retention_cutoff_date(
        current_date=current_date,
    )

    return closure_date < retention_cutoff_date


def cleanup_old_daily_operation_closures(
    db: Session,
    *,
    business_id: int | None = None,
    current_date: date | None = None,
) -> int:
    """Delete closure snapshots older than the retention policy.

    Items are deleted first because they reference the closure rows.
    The function flushes changes but leaves commit control to the caller.
    """

    retention_cutoff_date = get_daily_operation_closure_retention_cutoff_date(
        current_date=current_date,
    )

    filters = [
        DailyOperationClosure.closure_date < retention_cutoff_date,
    ]

    if business_id is not None:
        filters.append(DailyOperationClosure.business_id == business_id)

    old_closure_ids = list(
        db.execute(
            select(DailyOperationClosure.id).where(*filters)
        )
        .scalars()
        .all()
    )

    if not old_closure_ids:
        return 0

    db.execute(
        delete(DailyOperationClosureItem).where(
            DailyOperationClosureItem.closure_id.in_(old_closure_ids)
        )
    )

    db.execute(
        delete(DailyOperationClosure).where(
            DailyOperationClosure.id.in_(old_closure_ids)
        )
    )

    db.flush()

    return len(old_closure_ids)


def ensure_can_create_daily_operation_closure(current_user: User, *, business_id: int) -> None:
    ensure_business_scope(current_user, business_id)

    if current_user.role not in DAILY_OPERATION_CLOSURE_CREATORS:
        raise DailyOperationClosurePermissionError(
            "Günü sadece manager veya patron kapatabilir."
        )


def ensure_can_view_daily_operation_closure(current_user: User, *, business_id: int) -> None:
    ensure_business_scope(current_user, business_id)

    if current_user.role not in DAILY_OPERATION_CLOSURE_VIEWERS:
        raise DailyOperationClosurePermissionError(
            "Gün sonu raporunu görüntüleme yetkiniz yok."
        )


def get_business_timezone(business: Business) -> ZoneInfo:
    timezone_name = (business.timezone or "Asia/Nicosia").strip() or "Asia/Nicosia"

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Asia/Nicosia")


def get_business_now(business: Business, *, now_utc: datetime | None = None) -> datetime:
    source_now = now_utc or get_utc_now()

    if source_now.tzinfo is None:
        source_now = source_now.replace(tzinfo=timezone.utc)

    return source_now.astimezone(get_business_timezone(business))


def get_business_today(business: Business, *, now_utc: datetime | None = None) -> date:
    return get_business_now(business, now_utc=now_utc).date()


def parse_daily_closing_time(value: str | None) -> time:
    normalized_value = (value or "23:45").strip() or "23:45"
    hour_text, minute_text = normalized_value.split(":", maxsplit=1)
    hour = int(hour_text)
    minute = int(minute_text)

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("Otomatik kapanış saati geçersiz.")

    return time(hour=hour, minute=minute)


def is_business_ready_for_automatic_closure(
    business: Business,
    *,
    now_utc: datetime | None = None,
) -> bool:
    business_now = get_business_now(business, now_utc=now_utc)
    closing_time = parse_daily_closing_time(business.daily_closing_time)

    return business_now.time().replace(second=0, microsecond=0) >= closing_time


def get_daily_operation_closure_or_error(
    db: Session,
    *,
    closure_id: int,
) -> DailyOperationClosure:
    closure = db.get(DailyOperationClosure, closure_id)

    if closure is None:
        raise DailyOperationClosureNotFoundError("Gün sonu kapanış kaydı bulunamadı.")

    return closure


def get_existing_closure_for_date(
    db: Session,
    *,
    business_id: int,
    closure_date: date,
) -> DailyOperationClosure | None:
    return db.execute(
        select(DailyOperationClosure).where(
            DailyOperationClosure.business_id == business_id,
            DailyOperationClosure.closure_date == closure_date,
            DailyOperationClosure.status.in_(DAILY_OPERATION_CLOSURE_FINAL_STATUSES),
        )
    ).scalar_one_or_none()


def get_tasks_for_closure(
    db: Session,
    *,
    business_id: int,
    closure_date: date,
) -> list[Task]:
    return (
        db.execute(
            select(Task)
            .where(
                Task.business_id == business_id,
                Task.task_date == closure_date,
                Task.deleted_at_utc.is_(None),
            )
            .order_by(Task.assigned_to_user_id.asc(), Task.task_type.desc(), Task.id.asc())
        )
        .scalars()
        .all()
    )


def get_photo_evidence_task_ids(db: Session, *, task_ids: list[int]) -> set[int]:
    if not task_ids:
        return set()

    return set(
        db.execute(
            select(TaskAttachment.task_id)
            .where(
                TaskAttachment.task_id.in_(task_ids),
                TaskAttachment.attachment_type == TASK_ATTACHMENT_TYPE_EVIDENCE,
            )
            .group_by(TaskAttachment.task_id)
        )
        .scalars()
        .all()
    )


def build_user_snapshot_map(db: Session, *, tasks: list[Task]) -> dict[int, User]:
    user_ids = {
        task.assigned_to_user_id
        for task in tasks
        if task.assigned_to_user_id is not None
    }

    if not user_ids:
        return {}

    users = db.execute(select(User).where(User.id.in_(user_ids))).scalars().all()

    return {user.id: user for user in users}


def is_task_completed_for_metrics(task: Task) -> bool:
    if task.status == TASK_STATUS_APPROVED:
        return True

    if task.status == TASK_STATUS_COMPLETED:
        return True

    return False


def is_task_approval_pending(task: Task) -> bool:
    return task.status == TASK_STATUS_COMPLETED and task.requires_manager_approval


def is_task_open_or_problem_for_report(task: Task) -> bool:
    return task.status in OPEN_OR_PROBLEM_STATUSES


def calculate_closure_status(
    *,
    open_task_count: int,
    rejected_task_count: int,
    approval_pending_task_count: int,
    photo_required_task_count: int,
    photo_evidence_task_count: int,
) -> str:
    missing_photo_evidence_count = max(photo_required_task_count - photo_evidence_task_count, 0)

    has_issues = (
        open_task_count > 0
        or rejected_task_count > 0
        or approval_pending_task_count > 0
        or missing_photo_evidence_count > 0
    )

    if has_issues:
        return DAILY_OPERATION_CLOSURE_STATUS_WITH_ISSUES

    return DAILY_OPERATION_CLOSURE_STATUS_CLEAN


def validate_problematic_closure_note(
    *,
    closure_status: str,
    manager_note: str | None,
) -> None:
    if closure_status != DAILY_OPERATION_CLOSURE_STATUS_WITH_ISSUES:
        return

    if manager_note is None or not manager_note.strip():
        raise DailyOperationClosureNoteRequiredError(
            "Sorunlu gün kapanışında kapanış notu zorunludur."
        )


def create_daily_operation_closure(
    db: Session,
    *,
    current_user: User | None,
    business: Business,
    closure_date: date | None = None,
    manager_note: str | None = None,
    created_by_system: bool = False,
    allow_empty_day: bool = False,
) -> DailyOperationClosure:
    if not created_by_system:
        if current_user is None:
            raise DailyOperationClosurePermissionError(
                "Manuel gün kapanışı için kullanıcı bilgisi gereklidir."
            )

        ensure_can_create_daily_operation_closure(current_user, business_id=business.id)

    selected_closure_date = closure_date or get_business_today(business)

    existing_closure = get_existing_closure_for_date(
        db=db,
        business_id=business.id,
        closure_date=selected_closure_date,
    )

    if existing_closure is not None:
        raise DailyOperationClosureAlreadyExistsError(
            "Bu işletme için seçilen gün zaten kapatılmış."
        )

    tasks = get_tasks_for_closure(
        db=db,
        business_id=business.id,
        closure_date=selected_closure_date,
    )

    if not tasks and not allow_empty_day:
        raise DailyOperationClosureNotReadyError(
            "Bugün kapatılacak görev bulunamadı."
        )

    now = get_utc_now()
    photo_required_task_ids = [task.id for task in tasks if task.requires_photo]
    photo_evidence_task_ids = get_photo_evidence_task_ids(
        db=db,
        task_ids=photo_required_task_ids,
    )
    user_snapshot_map = build_user_snapshot_map(db=db, tasks=tasks)

    total_task_count = len(tasks)
    completed_task_count = sum(1 for task in tasks if is_task_completed_for_metrics(task))
    approved_task_count = sum(1 for task in tasks if task.status == TASK_STATUS_APPROVED)
    open_task_count = sum(1 for task in tasks if is_task_open_or_problem_for_report(task))
    rejected_task_count = sum(1 for task in tasks if task.status == TASK_STATUS_REJECTED)
    approval_pending_task_count = sum(1 for task in tasks if is_task_approval_pending(task))
    photo_required_task_count = len(photo_required_task_ids)
    photo_evidence_task_count = len(photo_evidence_task_ids)

    closure_status = calculate_closure_status(
        open_task_count=open_task_count,
        rejected_task_count=rejected_task_count,
        approval_pending_task_count=approval_pending_task_count,
        photo_required_task_count=photo_required_task_count,
        photo_evidence_task_count=photo_evidence_task_count,
    )

    if not created_by_system:
        validate_problematic_closure_note(
            closure_status=closure_status,
            manager_note=manager_note,
        )

    closure = DailyOperationClosure(
        business_id=business.id,
        closure_date=selected_closure_date,
        closed_by_user_id=current_user.id if current_user is not None else None,
        closed_by_user_full_name=(
            current_user.full_name if current_user is not None else "Missio Otomatik Sistem"
        ),
        closed_by_username=current_user.username if current_user is not None else "system",
        closed_by_role=current_user.role if current_user is not None else "system",
        closed_at_utc=now,
        status=closure_status,
        manager_note=manager_note,
        closed_by_system=created_by_system,
        total_task_count=total_task_count,
        completed_task_count=completed_task_count,
        approved_task_count=approved_task_count,
        open_task_count=open_task_count,
        rejected_task_count=rejected_task_count,
        approval_pending_task_count=approval_pending_task_count,
        photo_required_task_count=photo_required_task_count,
        photo_evidence_task_count=photo_evidence_task_count,
        created_at_utc=now,
    )

    db.add(closure)
    db.flush()

    for task in tasks:
        assigned_user = (
            user_snapshot_map.get(task.assigned_to_user_id)
            if task.assigned_to_user_id is not None
            else None
        )

        item = DailyOperationClosureItem(
            closure_id=closure.id,
            business_id=business.id,
            task_id=task.id,
            task_date=task.task_date,
            assigned_to_user_id=task.assigned_to_user_id,
            assigned_to_user_full_name=assigned_user.full_name if assigned_user else None,
            assigned_to_username=assigned_user.username if assigned_user else None,
            task_title=task.title,
            task_description=task.description,
            task_type=task.task_type,
            task_status=task.status,
            task_priority=task.priority,
            requires_photo=task.requires_photo,
            requires_location=task.requires_location,
            requires_manager_approval=task.requires_manager_approval,
            has_photo_evidence=task.id in photo_evidence_task_ids,
            assigned_at_utc=task.assigned_at_utc,
            started_at_utc=task.started_at_utc,
            completed_at_utc=task.completed_at_utc,
            approved_at_utc=task.approved_at_utc,
            created_at_utc=now,
        )

        db.add(item)

    db.flush()

    return closure


def create_automatic_daily_operation_closure_for_business(
    db: Session,
    *,
    business: Business,
    now_utc: datetime | None = None,
) -> AutomaticDailyClosureBusinessResult:
    selected_closure_date = get_business_today(business, now_utc=now_utc)

    existing_closure = get_existing_closure_for_date(
        db=db,
        business_id=business.id,
        closure_date=selected_closure_date,
    )

    if existing_closure is not None:
        return AutomaticDailyClosureBusinessResult(
            business_id=business.id,
            business_name=business.name,
            closure_date=selected_closure_date,
            status="skipped_already_closed",
            message="Bu işletmenin günü zaten kapatılmış.",
            closure_id=existing_closure.id,
        )

    if not is_business_ready_for_automatic_closure(business, now_utc=now_utc):
        return AutomaticDailyClosureBusinessResult(
            business_id=business.id,
            business_name=business.name,
            closure_date=selected_closure_date,
            status="skipped_before_closing_time",
            message="İşletmenin yerel otomatik kapanış saati henüz gelmedi.",
        )

    closure = create_daily_operation_closure(
        db=db,
        current_user=None,
        business=business,
        closure_date=selected_closure_date,
        manager_note="Bu gün, otomatik gün kapanışı ayarı açık olduğu için Missio tarafından sistemsel olarak kapatılmıştır.",
        created_by_system=True,
        allow_empty_day=True,
    )

    return AutomaticDailyClosureBusinessResult(
        business_id=business.id,
        business_name=business.name,
        closure_date=selected_closure_date,
        status="closed",
        message="Gün otomatik olarak kapatıldı ve rapor oluşturuldu.",
        closure_id=closure.id,
    )


def auto_close_enabled_businesses(
    db: Session,
    *,
    now_utc: datetime | None = None,
) -> AutomaticDailyClosureRunResult:
    businesses = (
        db.execute(
            select(Business).where(
                Business.is_active.is_(True),
                Business.auto_daily_closing_enabled.is_(True),
            )
        )
        .scalars()
        .all()
    )

    results: list[AutomaticDailyClosureBusinessResult] = []
    closed_count = 0
    failed_count = 0

    for business in businesses:
        try:
            result = create_automatic_daily_operation_closure_for_business(
                db=db,
                business=business,
                now_utc=now_utc,
            )
            results.append(result)

            if result.status == "closed":
                closed_count += 1
                db.commit()
            else:
                db.rollback()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            failed_count += 1
            results.append(
                AutomaticDailyClosureBusinessResult(
                    business_id=business.id,
                    business_name=business.name,
                    closure_date=None,
                    status="failed",
                    message=str(exc) or "Otomatik gün kapanışı başarısız oldu.",
                )
            )

    skipped_count = len(results) - closed_count - failed_count

    return AutomaticDailyClosureRunResult(
        checked_count=len(businesses),
        closed_count=closed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        results=results,
    )

def list_daily_operation_closures(
    db: Session,
    *,
    current_user: User,
    business: Business,
    limit: int = 100,
    offset: int = 0,
) -> DailyOperationClosureListResult:
    ensure_can_view_daily_operation_closure(current_user, business_id=business.id)

    retention_cutoff_date = get_daily_operation_closure_retention_cutoff_date()

    base_filters = [
        DailyOperationClosure.business_id == business.id,
        DailyOperationClosure.closure_date >= retention_cutoff_date,
    ]

    count_query = select(func.count(DailyOperationClosure.id)).where(*base_filters)

    query = select(DailyOperationClosure).where(*base_filters)

    total_count = int(db.execute(count_query).scalar_one())

    closures = (
        db.execute(
            query.order_by(
                DailyOperationClosure.closure_date.desc(),
                DailyOperationClosure.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return DailyOperationClosureListResult(
        closures=closures,
        total_count=total_count,
    )


def get_daily_operation_closure_detail(
    db: Session,
    *,
    current_user: User,
    closure_id: int,
) -> tuple[DailyOperationClosure, list[DailyOperationClosureItem]]:
    closure = get_daily_operation_closure_or_error(db=db, closure_id=closure_id)

    ensure_can_view_daily_operation_closure(
        current_user,
        business_id=closure.business_id,
    )

    if is_daily_operation_closure_expired(closure.closure_date):
        raise DailyOperationClosureNotFoundError(
            "Gün sonu kapanış kaydı 60 günlük saklama süresi dışında."
        )

    items = (
        db.execute(
            select(DailyOperationClosureItem)
            .where(DailyOperationClosureItem.closure_id == closure.id)
            .order_by(
                DailyOperationClosureItem.assigned_to_user_id.asc(),
                DailyOperationClosureItem.id.asc(),
            )
        )
        .scalars()
        .all()
    )

    return closure, items
