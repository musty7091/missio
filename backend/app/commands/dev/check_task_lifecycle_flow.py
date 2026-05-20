from __future__ import annotations

from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.schemas.task import (
    TASK_STATUS_APPROVED,
    TASK_STATUS_ASSIGNED,
    TASK_STATUS_CANCELLED,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_REJECTED,
)
from app.services.task_service import (
    approve_task,
    cancel_task,
    complete_task,
    create_extra_task,
    get_business_today,
    reject_task,
    soft_delete_task,
    start_task,
)


BUSINESS_SLUG = "missio-demo-market"
OWNER_USERNAME = "owner"
STAFF_USERNAME = "ahmet"

TASK_TITLE_APPROVE_FLOW = "LIFECYCLE DEMO - Onay akışı"
TASK_TITLE_REJECT_FLOW = "LIFECYCLE DEMO - Red ve tekrar tamamlama akışı"
TASK_TITLE_CANCEL_FLOW = "LIFECYCLE DEMO - İptal akışı"
TASK_TITLE_DELETE_FLOW = "LIFECYCLE DEMO - Silme akışı"


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


def cleanup_lifecycle_demo_tasks(db, *, business_id: int) -> None:
    """Delete old lifecycle demo tasks and their events."""

    demo_titles = [
        TASK_TITLE_APPROVE_FLOW,
        TASK_TITLE_REJECT_FLOW,
        TASK_TITLE_CANCEL_FLOW,
        TASK_TITLE_DELETE_FLOW,
    ]

    old_tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title.in_(demo_titles),
            )
        )
        .scalars()
        .all()
    )

    old_task_ids = [task.id for task in old_tasks]

    if old_task_ids:
        db.execute(delete(TaskEvent).where(TaskEvent.task_id.in_(old_task_ids)))
        db.execute(delete(Task).where(Task.id.in_(old_task_ids)))

    db.commit()


def assert_task_status(
    task: Task,
    *,
    expected_status: str,
    label: str,
) -> None:
    """Validate task status."""

    if task.status != expected_status:
        raise RuntimeError(
            f"{label} durum hatası. "
            f"Beklenen: {expected_status}, Gelen: {task.status}"
        )


def create_lifecycle_task(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
    title: str,
) -> Task:
    """Create lifecycle demo extra task."""

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=staff,
        title=title,
        description="Görev yaşam döngüsü demo kontrolü için oluşturuldu.",
        requires_photo=False,
        requires_location=False,
        requires_manager_approval=True,
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )

    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_ASSIGNED,
        label=f"{title} oluşturma",
    )

    return task


def check_approve_flow(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> None:
    """Check assigned -> in_progress -> completed -> approved flow."""

    task = create_lifecycle_task(
        db=db,
        owner=owner,
        business=business,
        staff=staff,
        title=TASK_TITLE_APPROVE_FLOW,
    )

    task = start_task(
        db=db,
        current_user=staff,
        task=task,
        note="Personel göreve başladı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_IN_PROGRESS,
        label="Onay akışı başlatma",
    )

    task = complete_task(
        db=db,
        current_user=staff,
        task=task,
        note="Personel görevi tamamladı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_COMPLETED,
        label="Onay akışı tamamlama",
    )

    task = approve_task(
        db=db,
        current_user=owner,
        task=task,
        note="Owner görevi onayladı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_APPROVED,
        label="Onay akışı onaylama",
    )

    print("[OK] Yaşam döngüsü onay akışı başarılı.")


def check_reject_and_recomplete_flow(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> None:
    """Check completed -> rejected -> completed -> approved flow."""

    task = create_lifecycle_task(
        db=db,
        owner=owner,
        business=business,
        staff=staff,
        title=TASK_TITLE_REJECT_FLOW,
    )

    task = start_task(
        db=db,
        current_user=staff,
        task=task,
        note="Personel göreve başladı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_IN_PROGRESS,
        label="Red akışı başlatma",
    )

    task = complete_task(
        db=db,
        current_user=staff,
        task=task,
        note="Personel görevi tamamladı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_COMPLETED,
        label="Red akışı ilk tamamlama",
    )

    task = reject_task(
        db=db,
        current_user=owner,
        task=task,
        note="Eksik bulundu, tekrar yapılmalı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_REJECTED,
        label="Red akışı reddetme",
    )

    task = complete_task(
        db=db,
        current_user=staff,
        task=task,
        note="Eksikler giderildi ve tekrar tamamlandı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_COMPLETED,
        label="Red akışı tekrar tamamlama",
    )

    task = approve_task(
        db=db,
        current_user=owner,
        task=task,
        note="Eksikler giderildi, görev onaylandı.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_APPROVED,
        label="Red akışı final onay",
    )

    print("[OK] Yaşam döngüsü red ve tekrar tamamlama akışı başarılı.")


def check_cancel_flow(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> None:
    """Check assigned -> cancelled flow."""

    task = create_lifecycle_task(
        db=db,
        owner=owner,
        business=business,
        staff=staff,
        title=TASK_TITLE_CANCEL_FLOW,
    )

    task = cancel_task(
        db=db,
        current_user=owner,
        task=task,
        note="Görev artık gerekli olmadığı için iptal edildi.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    assert_task_status(
        task,
        expected_status=TASK_STATUS_CANCELLED,
        label="İptal akışı",
    )

    print("[OK] Yaşam döngüsü iptal akışı başarılı.")


def check_soft_delete_flow(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> None:
    """Check soft delete flow."""

    task = create_lifecycle_task(
        db=db,
        owner=owner,
        business=business,
        staff=staff,
        title=TASK_TITLE_DELETE_FLOW,
    )

    task = soft_delete_task(
        db=db,
        current_user=owner,
        task=task,
        note="Demo görev soft delete ile silindi.",
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_lifecycle_flow",
    )
    db.commit()
    db.refresh(task)

    if task.deleted_at_utc is None:
        raise RuntimeError("Soft delete akışı başarısız. deleted_at_utc boş kaldı.")

    print("[OK] Yaşam döngüsü soft delete akışı başarılı.")


def print_lifecycle_event_summary(db, *, business_id: int) -> None:
    """Print lifecycle task event summary."""

    demo_titles = [
        TASK_TITLE_APPROVE_FLOW,
        TASK_TITLE_REJECT_FLOW,
        TASK_TITLE_CANCEL_FLOW,
        TASK_TITLE_DELETE_FLOW,
    ]

    tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title.in_(demo_titles),
            )
        )
        .scalars()
        .all()
    )

    task_ids = [task.id for task in tasks]

    events = []

    if task_ids:
        events = (
            db.execute(
                select(TaskEvent)
                .where(TaskEvent.task_id.in_(task_ids))
                .order_by(TaskEvent.task_id.asc(), TaskEvent.id.asc())
            )
            .scalars()
            .all()
        )

    print("")
    print("Yaşam Döngüsü Event Özeti")
    print("-------------------------")

    if not events:
        print("(event kaydı yok)")
        return

    for event in events:
        print(
            f"task_id={event.task_id} | "
            f"event={event.event_type} | "
            f"old={event.old_status} | "
            f"new={event.new_status}"
        )


def main() -> None:
    """Run task lifecycle demo flow checks."""

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

        task_date = get_business_today(business)

        print("[INFO] Missio görev yaşam döngüsü kontrolü başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev tarihi: {task_date}")
        print(f"[INFO] Owner: {owner.username} ({owner.role})")
        print(f"[INFO] Staff: {staff.username} ({staff.role})")

        cleanup_lifecycle_demo_tasks(db, business_id=business.id)

        check_approve_flow(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        check_reject_and_recomplete_flow(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        check_cancel_flow(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        check_soft_delete_flow(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        print_lifecycle_event_summary(db, business_id=business.id)

        print("")
        print("[OK] Missio görev yaşam döngüsü demo kontrolü başarılı.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()