from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image
from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.commands.cleanup_old_task_attachments import (
    CLEANUP_EVENT_TYPE,
    run_cleanup,
)
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.models.task_event import TaskEvent
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.schemas.task import (
    TASK_STATUS_APPROVED,
    TASK_STATUS_CANCELLED,
    TASK_STATUS_COMPLETED,
)
from app.services.task_attachment_service import TASK_ATTACHMENT_STORAGE_ROOT
from app.services.task_service import create_extra_task


BUSINESS_SLUG = "missio-demo-market"
OWNER_USERNAME = "owner"
STAFF_USERNAME = "ahmet"

TASK_TITLE_APPROVED_CLEANUP = "CLEANUP DEMO - Approved eski fotoğraf"
TASK_TITLE_CANCELLED_CLEANUP = "CLEANUP DEMO - Cancelled eski fotoğraf"
TASK_TITLE_COMPLETED_PROTECTED = "CLEANUP DEMO - Completed korunacak fotoğraf"

DEMO_TASK_TITLES = {
    TASK_TITLE_APPROVED_CLEANUP,
    TASK_TITLE_CANCELLED_CLEANUP,
    TASK_TITLE_COMPLETED_PROTECTED,
}


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def get_demo_business(db) -> Business:
    """Return demo business."""

    business = (
        db.execute(select(Business).where(Business.slug == BUSINESS_SLUG))
        .scalars()
        .first()
    )

    if business is None:
        raise RuntimeError(
            "Demo işletme bulunamadı. Önce şu komutu çalıştırın: "
            "python -m app.commands.dev.seed_local_task_demo_data"
        )

    return business


def get_demo_user(
    db,
    *,
    business_id: int,
    username: str,
) -> User:
    """Return demo business user."""

    user = (
        db.execute(
            select(User).where(
                User.business_id == business_id,
                User.username == normalize_username(username),
            )
        )
        .scalars()
        .first()
    )

    if user is None:
        raise RuntimeError(
            f"Demo kullanıcı bulunamadı: {username}. "
            "Önce şu komutu çalıştırın: "
            "python -m app.commands.dev.seed_local_task_demo_data"
        )

    return user


def delete_file_if_safe(file_path: str | None) -> None:
    """Delete file if it exists under task attachment storage root."""

    if not file_path:
        return

    path = Path(file_path)

    if path.is_absolute():
        return

    normalized_path = path.as_posix()
    storage_root = TASK_ATTACHMENT_STORAGE_ROOT.as_posix()

    if not normalized_path.startswith(storage_root + "/"):
        return

    if path.exists() and path.is_file():
        path.unlink()


def cleanup_old_demo_data(db, *, business_id: int) -> None:
    """Delete old cleanup demo data."""

    old_tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title.in_(DEMO_TASK_TITLES),
            )
        )
        .scalars()
        .all()
    )

    old_task_ids = [task.id for task in old_tasks]

    if not old_task_ids:
        db.commit()
        return

    old_attachments = (
        db.execute(
            select(TaskAttachment).where(TaskAttachment.task_id.in_(old_task_ids))
        )
        .scalars()
        .all()
    )

    for attachment in old_attachments:
        delete_file_if_safe(attachment.file_path)

    db.execute(delete(TaskAttachment).where(TaskAttachment.task_id.in_(old_task_ids)))
    db.execute(delete(TaskEvent).where(TaskEvent.task_id.in_(old_task_ids)))
    db.execute(delete(Task).where(Task.id.in_(old_task_ids)))
    db.commit()


def create_demo_jpeg_bytes() -> bytes:
    """Create small in-memory demo JPEG image."""

    image = Image.new("RGB", (900, 650), (240, 240, 240))

    for x in range(50, 850, 100):
        for y in range(50, 600, 100):
            for dx in range(45):
                for dy in range(45):
                    image.putpixel((x + dx, y + dy), (180, 180, 180))

    output = BytesIO()
    image.save(output, format="JPEG", quality=85)

    return output.getvalue()


def create_task_for_cleanup_check(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
    title: str,
    status: str,
    age_days: int,
) -> Task:
    """Create demo task and force selected status/date."""

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=staff,
        title=title,
        description="Fotoğraf temizlik kontrolü için oluşturulan demo görev.",
        requires_photo=True,
        requires_location=False,
        requires_manager_approval=True,
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_attachment_cleanup_flow",
    )

    reference_datetime = get_utc_now() - timedelta(days=age_days)

    task.status = status
    task.updated_at_utc = reference_datetime

    if status in {
        TASK_STATUS_APPROVED,
        TASK_STATUS_COMPLETED,
    }:
        task.completed_at_utc = reference_datetime

    if status == TASK_STATUS_APPROVED:
        task.approved_at_utc = reference_datetime

    db.add(task)
    db.flush()

    return task


def create_attachment_for_task(
    db,
    *,
    task: Task,
    uploaded_by_user: User,
) -> TaskAttachment:
    """Create physical demo file and attachment record."""

    content = create_demo_jpeg_bytes()

    storage_directory = (
        TASK_ATTACHMENT_STORAGE_ROOT
        / "cleanup_check"
        / f"business_{task.business_id}"
        / f"task_{task.id}"
    )
    storage_directory.mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid4()}.jpg"
    file_path = storage_directory / file_name
    file_path.write_bytes(content)

    attachment = TaskAttachment(
        business_id=task.business_id,
        task_id=task.id,
        event_id=None,
        uploaded_by_user_id=uploaded_by_user.id,
        file_path=file_path.as_posix(),
        file_name=file_name,
        file_type="image/jpeg",
        file_size=len(content),
        latitude=None,
        longitude=None,
        location_accuracy=None,
        created_at_utc=get_utc_now() - timedelta(days=20),
    )

    db.add(attachment)
    db.flush()

    return attachment


def assert_attachment_exists(
    db,
    *,
    attachment_id: int,
    file_path: str,
    label: str,
) -> None:
    """Validate attachment record and physical file exist."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is None:
        raise RuntimeError(f"{label}: attachment kaydı bulunamadı.")

    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise RuntimeError(f"{label}: fiziksel dosya bulunamadı. file_path={file_path}")


def assert_attachment_deleted(
    db,
    *,
    attachment_id: int,
    file_path: str,
    label: str,
) -> None:
    """Validate attachment record and physical file are deleted."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is not None:
        raise RuntimeError(f"{label}: attachment kaydı hâlâ duruyor.")

    path = Path(file_path)

    if path.exists():
        raise RuntimeError(f"{label}: fiziksel dosya hâlâ duruyor. file_path={file_path}")


def assert_cleanup_event_exists(
    db,
    *,
    task_id: int,
    label: str,
) -> None:
    """Validate cleanup event exists for task."""

    db.expire_all()

    event = (
        db.execute(
            select(TaskEvent).where(
                TaskEvent.task_id == task_id,
                TaskEvent.event_type == CLEANUP_EVENT_TYPE,
            )
        )
        .scalars()
        .first()
    )

    if event is None:
        raise RuntimeError(f"{label}: cleanup event kaydı bulunamadı.")


def main() -> None:
    """Check old task attachment cleanup flow."""

    db = SessionLocal()

    try:
        business = get_demo_business(db)
        owner = get_demo_user(
            db=db,
            business_id=business.id,
            username=OWNER_USERNAME,
        )
        staff = get_demo_user(
            db=db,
            business_id=business.id,
            username=STAFF_USERNAME,
        )

        cleanup_old_demo_data(db, business_id=business.id)

        approved_task = create_task_for_cleanup_check(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
            title=TASK_TITLE_APPROVED_CLEANUP,
            status=TASK_STATUS_APPROVED,
            age_days=20,
        )
        approved_attachment = create_attachment_for_task(
            db=db,
            task=approved_task,
            uploaded_by_user=staff,
        )

        cancelled_task = create_task_for_cleanup_check(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
            title=TASK_TITLE_CANCELLED_CLEANUP,
            status=TASK_STATUS_CANCELLED,
            age_days=10,
        )
        cancelled_attachment = create_attachment_for_task(
            db=db,
            task=cancelled_task,
            uploaded_by_user=staff,
        )

        completed_task = create_task_for_cleanup_check(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
            title=TASK_TITLE_COMPLETED_PROTECTED,
            status=TASK_STATUS_COMPLETED,
            age_days=30,
        )
        completed_attachment = create_attachment_for_task(
            db=db,
            task=completed_task,
            uploaded_by_user=staff,
        )

        db.commit()

        approved_attachment_id = approved_attachment.id
        approved_file_path = approved_attachment.file_path
        approved_task_id = approved_task.id

        cancelled_attachment_id = cancelled_attachment.id
        cancelled_file_path = cancelled_attachment.file_path
        cancelled_task_id = cancelled_task.id

        completed_attachment_id = completed_attachment.id
        completed_file_path = completed_attachment.file_path

        print("[INFO] Görev fotoğraf temizlik kontrolü başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Approved demo attachment_id={approved_attachment_id}")
        print(f"[INFO] Cancelled demo attachment_id={cancelled_attachment_id}")
        print(f"[INFO] Completed korunacak attachment_id={completed_attachment_id}")

        dry_run_result = run_cleanup(
            approved_retention_days=15,
            cancelled_retention_days=7,
            business_id=business.id,
            limit=1000,
            apply_changes=False,
        )

        if dry_run_result.candidate_count < 2:
            raise RuntimeError(
                "Dry-run temizlik adayı beklenenden az. "
                f"Beklenen en az: 2, Gelen: {dry_run_result.candidate_count}"
            )

        if dry_run_result.deleted_count != 0:
            raise RuntimeError("Dry-run modunda silinen kayıt olmamalı.")

        assert_attachment_exists(
            db,
            attachment_id=approved_attachment_id,
            file_path=approved_file_path,
            label="Dry-run approved kontrol",
        )
        assert_attachment_exists(
            db,
            attachment_id=cancelled_attachment_id,
            file_path=cancelled_file_path,
            label="Dry-run cancelled kontrol",
        )
        assert_attachment_exists(
            db,
            attachment_id=completed_attachment_id,
            file_path=completed_file_path,
            label="Dry-run completed kontrol",
        )

        print("[OK] Dry-run modu doğru çalıştı; hiçbir dosya silinmedi.")

        apply_result = run_cleanup(
            approved_retention_days=15,
            cancelled_retention_days=7,
            business_id=business.id,
            limit=1000,
            apply_changes=True,
        )

        if apply_result.deleted_count < 2:
            raise RuntimeError(
                "Apply modunda beklenen sayıda kayıt silinmedi. "
                f"Beklenen en az: 2, Gelen: {apply_result.deleted_count}"
            )

        assert_attachment_deleted(
            db,
            attachment_id=approved_attachment_id,
            file_path=approved_file_path,
            label="Apply approved kontrol",
        )
        assert_attachment_deleted(
            db,
            attachment_id=cancelled_attachment_id,
            file_path=cancelled_file_path,
            label="Apply cancelled kontrol",
        )
        assert_attachment_exists(
            db,
            attachment_id=completed_attachment_id,
            file_path=completed_file_path,
            label="Apply completed korunma kontrol",
        )

        assert_cleanup_event_exists(
            db,
            task_id=approved_task_id,
            label="Approved cleanup event kontrol",
        )
        assert_cleanup_event_exists(
            db,
            task_id=cancelled_task_id,
            label="Cancelled cleanup event kontrol",
        )

        print("[OK] Approved eski fotoğraf temizlendi.")
        print("[OK] Cancelled eski fotoğraf temizlendi.")
        print("[OK] Completed durumundaki fotoğrafa dokunulmadı.")
        print("[OK] Cleanup event kayıtları doğrulandı.")
        print("")
        print("[OK] Görev fotoğraf temizlik akışı başarılı.")
    finally:
        db.close()


if __name__ == "__main__":
    main()