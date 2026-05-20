from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.schemas.task import (
    TASK_STATUS_APPROVED,
    TASK_STATUS_CANCELLED,
)
from app.services.task_attachment_service import TASK_ATTACHMENT_STORAGE_ROOT
from app.services.task_service import create_task_event


DEFAULT_APPROVED_RETENTION_DAYS = 15
DEFAULT_CANCELLED_RETENTION_DAYS = 7
DEFAULT_LIMIT = 1000

CLEANUP_EVENT_TYPE = "task_attachment_cleaned_up"


@dataclass(frozen=True)
class CleanupCandidate:
    """Attachment cleanup candidate."""

    task: Task
    attachment: TaskAttachment
    cleanup_reason: str
    reference_datetime_utc: datetime
    retention_days: int


@dataclass(frozen=True)
class CleanupResult:
    """Cleanup command result."""

    checked_count: int
    candidate_count: int
    deleted_count: int
    skipped_count: int
    dry_run: bool


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def normalize_datetime_to_utc(value: datetime | None) -> datetime | None:
    """Normalize datetime value to timezone-aware UTC."""

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def get_task_cleanup_reference_datetime(task: Task) -> datetime | None:
    """Return task cleanup reference datetime."""

    if task.status == TASK_STATUS_APPROVED:
        return (
            normalize_datetime_to_utc(task.approved_at_utc)
            or normalize_datetime_to_utc(task.updated_at_utc)
            or normalize_datetime_to_utc(task.completed_at_utc)
            or normalize_datetime_to_utc(task.created_at_utc)
        )

    if task.status == TASK_STATUS_CANCELLED:
        return (
            normalize_datetime_to_utc(task.updated_at_utc)
            or normalize_datetime_to_utc(task.created_at_utc)
        )

    return None


def get_task_retention_days(
    task: Task,
    *,
    approved_retention_days: int,
    cancelled_retention_days: int,
) -> int | None:
    """Return retention days for task status."""

    if task.status == TASK_STATUS_APPROVED:
        return approved_retention_days

    if task.status == TASK_STATUS_CANCELLED:
        return cancelled_retention_days

    return None


def get_task_cleanup_reason(task: Task) -> str | None:
    """Return cleanup reason for task status."""

    if task.status == TASK_STATUS_APPROVED:
        return "approved_retention_expired"

    if task.status == TASK_STATUS_CANCELLED:
        return "cancelled_retention_expired"

    return None


def is_attachment_file_path_safe(file_path: str) -> bool:
    """Return whether attachment file path is safely under storage root."""

    path = Path(file_path)

    if path.is_absolute():
        return False

    normalized_path = path.as_posix()
    storage_root = TASK_ATTACHMENT_STORAGE_ROOT.as_posix()

    return normalized_path.startswith(storage_root + "/")


def delete_physical_file_if_exists(file_path: str) -> bool:
    """Delete physical attachment file if it exists, return whether file was deleted."""

    path = Path(file_path)

    if path.exists() and path.is_file():
        path.unlink()
        return True

    return False


def get_business_filter(
    db: Session,
    *,
    business_id: int | None,
) -> int | None:
    """Validate and return optional business filter."""

    if business_id is None:
        return None

    business = db.get(Business, business_id)

    if business is None:
        raise RuntimeError(f"İşletme bulunamadı. business_id={business_id}")

    return business.id


def collect_cleanup_candidates(
    db: Session,
    *,
    now_utc: datetime,
    approved_retention_days: int,
    cancelled_retention_days: int,
    business_id: int | None,
    limit: int,
) -> tuple[int, list[CleanupCandidate]]:
    """Collect old task attachment cleanup candidates."""

    query = (
        select(TaskAttachment, Task)
        .join(Task, TaskAttachment.task_id == Task.id)
        .where(
            Task.status.in_(
                {
                    TASK_STATUS_APPROVED,
                    TASK_STATUS_CANCELLED,
                }
            )
        )
        .order_by(TaskAttachment.id.asc())
        .limit(limit)
    )

    if business_id is not None:
        query = query.where(TaskAttachment.business_id == business_id)

    rows = db.execute(query).all()

    candidates: list[CleanupCandidate] = []

    for attachment, task in rows:
        reference_datetime_utc = get_task_cleanup_reference_datetime(task)
        retention_days = get_task_retention_days(
            task,
            approved_retention_days=approved_retention_days,
            cancelled_retention_days=cancelled_retention_days,
        )
        cleanup_reason = get_task_cleanup_reason(task)

        if reference_datetime_utc is None:
            continue

        if retention_days is None:
            continue

        if cleanup_reason is None:
            continue

        cutoff_datetime_utc = now_utc - timedelta(days=retention_days)

        if reference_datetime_utc > cutoff_datetime_utc:
            continue

        candidates.append(
            CleanupCandidate(
                task=task,
                attachment=attachment,
                cleanup_reason=cleanup_reason,
                reference_datetime_utc=reference_datetime_utc,
                retention_days=retention_days,
            )
        )

    return len(rows), candidates


def print_candidate(candidate: CleanupCandidate, *, dry_run: bool) -> None:
    """Print cleanup candidate."""

    prefix = "[DRY-RUN]" if dry_run else "[DELETE]"

    print(
        f"{prefix} "
        f"business_id={candidate.attachment.business_id} | "
        f"task_id={candidate.task.id} | "
        f"task_status={candidate.task.status} | "
        f"attachment_id={candidate.attachment.id} | "
        f"retention_days={candidate.retention_days} | "
        f"reason={candidate.cleanup_reason} | "
        f"file_path={candidate.attachment.file_path}"
    )


def cleanup_candidate(
    db: Session,
    *,
    candidate: CleanupCandidate,
) -> bool:
    """Clean a single candidate. Return True if record is deleted."""

    attachment = candidate.attachment
    task = candidate.task

    if not is_attachment_file_path_safe(attachment.file_path):
        print(
            "[WARN] Güvensiz dosya yolu nedeniyle atlandı. "
            f"attachment_id={attachment.id}, file_path={attachment.file_path}"
        )
        return False

    physical_file_deleted = delete_physical_file_if_exists(attachment.file_path)

    create_task_event(
        db=db,
        task=task,
        user_id=None,
        event_type=CLEANUP_EVENT_TYPE,
        old_status=task.status,
        new_status=task.status,
        note=(
            "Görev fotoğraf kanıtı saklama politikası nedeniyle temizlendi. "
            f"attachment_id={attachment.id}; "
            f"reason={candidate.cleanup_reason}; "
            f"retention_days={candidate.retention_days}; "
            f"physical_file_deleted={physical_file_deleted}"
        ),
        ip_address=None,
        user_agent="Missio command cleanup_old_task_attachments",
    )

    db.delete(attachment)

    return True


def run_cleanup(
    *,
    approved_retention_days: int,
    cancelled_retention_days: int,
    business_id: int | None,
    limit: int,
    apply_changes: bool,
) -> CleanupResult:
    """Run task attachment cleanup."""

    db = SessionLocal()

    try:
        validated_business_id = get_business_filter(
            db,
            business_id=business_id,
        )

        now_utc = get_utc_now()

        checked_count, candidates = collect_cleanup_candidates(
            db,
            now_utc=now_utc,
            approved_retention_days=approved_retention_days,
            cancelled_retention_days=cancelled_retention_days,
            business_id=validated_business_id,
            limit=limit,
        )

        deleted_count = 0
        skipped_count = 0

        for candidate in candidates:
            print_candidate(candidate, dry_run=not apply_changes)

            if not apply_changes:
                continue

            is_deleted = cleanup_candidate(
                db=db,
                candidate=candidate,
            )

            if is_deleted:
                deleted_count += 1
            else:
                skipped_count += 1

        if apply_changes:
            db.commit()
        else:
            db.rollback()

        return CleanupResult(
            checked_count=checked_count,
            candidate_count=len(candidates),
            deleted_count=deleted_count,
            skipped_count=skipped_count,
            dry_run=not apply_changes,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Clean old Missio task attachment files according to retention policy."
    )

    parser.add_argument(
        "--approved-days",
        type=int,
        default=DEFAULT_APPROVED_RETENTION_DAYS,
        help=(
            "Approved görev fotoğrafları için saklama süresi. "
            f"Varsayılan: {DEFAULT_APPROVED_RETENTION_DAYS}"
        ),
    )
    parser.add_argument(
        "--cancelled-days",
        type=int,
        default=DEFAULT_CANCELLED_RETENTION_DAYS,
        help=(
            "Cancelled görev fotoğrafları için saklama süresi. "
            f"Varsayılan: {DEFAULT_CANCELLED_RETENTION_DAYS}"
        ),
    )
    parser.add_argument(
        "--business-id",
        type=int,
        default=None,
        help="Sadece belirli bir işletmenin fotoğraflarını kontrol eder.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Tek çalıştırmada kontrol edilecek maksimum kayıt. Varsayılan: {DEFAULT_LIMIT}",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Gerçek silme işlemini yapar. Bu parametre yoksa sadece dry-run çalışır.",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""

    if args.approved_days < 1:
        raise RuntimeError("--approved-days en az 1 olmalıdır.")

    if args.cancelled_days < 1:
        raise RuntimeError("--cancelled-days en az 1 olmalıdır.")

    if args.limit < 1:
        raise RuntimeError("--limit en az 1 olmalıdır.")

    if args.business_id is not None and args.business_id < 1:
        raise RuntimeError("--business-id pozitif bir sayı olmalıdır.")


def main() -> None:
    """Command entrypoint."""

    args = parse_args()
    validate_args(args)

    print("[INFO] Missio eski görev fotoğraf temizleme komutu başladı.")

    if args.apply:
        print("[INFO] Mod: APPLY | Gerçek silme yapılacak.")
    else:
        print("[INFO] Mod: DRY-RUN | Silme yapılmayacak, sadece adaylar gösterilecek.")

    print(f"[INFO] Approved saklama süresi: {args.approved_days} gün")
    print(f"[INFO] Cancelled saklama süresi: {args.cancelled_days} gün")
    print(f"[INFO] Limit: {args.limit}")

    if args.business_id is not None:
        print(f"[INFO] Business filtresi: business_id={args.business_id}")

    result = run_cleanup(
        approved_retention_days=args.approved_days,
        cancelled_retention_days=args.cancelled_days,
        business_id=args.business_id,
        limit=args.limit,
        apply_changes=args.apply,
    )

    print("")
    print("[OK] Temizlik kontrolü tamamlandı.")
    print(f"[OK] Kontrol edilen kayıt: {result.checked_count}")
    print(f"[OK] Temizlik adayı: {result.candidate_count}")
    print(f"[OK] Silinen kayıt: {result.deleted_count}")
    print(f"[OK] Atlanan kayıt: {result.skipped_count}")

    if result.dry_run:
        print("")
        print("[INFO] Bu sadece dry-run idi. Gerçek silme için:")
        print("python -m app.commands.cleanup_old_task_attachments --apply")


if __name__ == "__main__":
    main()