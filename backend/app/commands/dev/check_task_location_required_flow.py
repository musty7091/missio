from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.api.dependencies import get_current_user
from app.db.session import SessionLocal, get_db
from app.main import app
from app.models.business import Business
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.models.task_event import TaskEvent
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.schemas.task import (
    TASK_STATUS_APPROVED,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_IN_PROGRESS,
)
from app.services.task_service import create_extra_task


BUSINESS_SLUG = "missio-demo-market"
OWNER_USERNAME = "owner"
STAFF_USERNAME = "ahmet"

TASK_TITLE_LOCATION_REQUIRED_FLOW = "LOCATION REQUIRED DEMO - Konum zorunlu görev akışı"

START_LATITUDE = 36.8000
START_LONGITUDE = 34.6333
START_LOCATION_ACCURACY = 20.0

COMPLETE_LATITUDE = 36.8010
COMPLETE_LONGITUDE = 34.6340
COMPLETE_LOCATION_ACCURACY = 18.0

EXPECTED_EVENT_TYPES = {
    "extra_task_created",
    "task_started",
    "task_completed",
    "task_approved",
}


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
    """Delete demo file if it exists under storage directory."""

    if not file_path:
        return

    path = Path(file_path)

    if path.is_absolute():
        return

    normalized_path = path.as_posix()

    if not normalized_path.startswith("storage/task_attachments/"):
        return

    if path.exists() and path.is_file():
        path.unlink()


def cleanup_old_demo_data(db, *, business_id: int) -> None:
    """Delete old location required demo data."""

    old_tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title == TASK_TITLE_LOCATION_REQUIRED_FLOW,
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


def create_location_required_task(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> Task:
    """Create fresh location required demo task."""

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=staff,
        title=TASK_TITLE_LOCATION_REQUIRED_FLOW,
        description="Konum zorunlu görev kuralı için demo görev.",
        requires_photo=False,
        requires_location=True,
        requires_manager_approval=True,
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_location_required_flow",
    )

    db.commit()
    db.refresh(task)

    return task


def build_get_db_override():
    """Build database dependency override."""

    def override_get_db():
        db = SessionLocal()

        try:
            yield db
        finally:
            db.close()

    return override_get_db


def build_get_current_user_override(user_id: int):
    """Build current user dependency override."""

    def override_get_current_user():
        db = SessionLocal()

        try:
            fresh_user = db.get(User, user_id)

            if fresh_user is None:
                raise RuntimeError("Override kullanıcısı veritabanında bulunamadı.")

            return fresh_user
        finally:
            db.close()

    return override_get_current_user


def set_current_user_override(user: User) -> None:
    """Set FastAPI dependency overrides for selected user."""

    app.dependency_overrides[get_db] = build_get_db_override()
    app.dependency_overrides[get_current_user] = build_get_current_user_override(user.id)


def assert_task_status(
    db,
    *,
    task_id: int,
    expected_status: str,
    label: str,
) -> None:
    """Validate task status from database."""

    db.expire_all()

    task = db.get(Task, task_id)

    if task is None:
        raise RuntimeError(f"{label}: görev bulunamadı.")

    if task.status != expected_status:
        raise RuntimeError(
            f"{label}: görev durumu hatalı. "
            f"Beklenen: {expected_status}, Gelen: {task.status}"
        )


def try_start_without_location_should_fail(
    *,
    staff: User,
    task_id: int,
) -> None:
    """Try to start task without location and expect failure."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/start",
        json={
            "note": "Konum olmadan başlatmaya çalışıyorum.",
        },
    )

    if response.status_code != 400:
        raise RuntimeError(
            "Konumsuz başlatma başarısız olmalıydı ama beklenen hata gelmedi. "
            f"HTTP {response.status_code}: {response.text}"
        )

    detail = str(response.json().get("detail", ""))

    if "konum" not in detail.lower():
        raise RuntimeError(
            "Konumsuz başlatma hatası beklenen açıklamayı içermiyor. "
            f"detail={detail}"
        )

    print("[OK] Konum yokken görev başlatılamadı.")


def start_with_location(
    *,
    staff: User,
    task_id: int,
) -> None:
    """Start task with location through API as assigned staff."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/start",
        json={
            "note": "Konum bilgisiyle göreve başladım.",
            "latitude": START_LATITUDE,
            "longitude": START_LONGITUDE,
            "location_accuracy": START_LOCATION_ACCURACY,
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Konumlu görev başlatma endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    task = response.json().get("task")

    if not isinstance(task, dict):
        raise RuntimeError("Konumlu başlatma cevabında task nesnesi yok.")

    if task.get("status") != TASK_STATUS_IN_PROGRESS:
        raise RuntimeError(
            "Konumlu başlatma sonrası status hatalı. "
            f"Gelen: {task.get('status')}"
        )

    print("[OK] Konum bilgisiyle görev başlatıldı.")


def try_complete_without_location_should_fail(
    *,
    staff: User,
    task_id: int,
) -> None:
    """Try to complete task without location and expect failure."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={
            "note": "Konum olmadan tamamlamaya çalışıyorum.",
        },
    )

    if response.status_code != 400:
        raise RuntimeError(
            "Konumsuz tamamlama başarısız olmalıydı ama beklenen hata gelmedi. "
            f"HTTP {response.status_code}: {response.text}"
        )

    detail = str(response.json().get("detail", ""))

    if "konum" not in detail.lower():
        raise RuntimeError(
            "Konumsuz tamamlama hatası beklenen açıklamayı içermiyor. "
            f"detail={detail}"
        )

    print("[OK] Konum yokken görev tamamlanamadı.")


def complete_with_location(
    *,
    staff: User,
    task_id: int,
) -> None:
    """Complete task with location through API as assigned staff."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={
            "note": "Konum bilgisiyle görevi tamamladım.",
            "latitude": COMPLETE_LATITUDE,
            "longitude": COMPLETE_LONGITUDE,
            "location_accuracy": COMPLETE_LOCATION_ACCURACY,
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Konumlu görev tamamlama endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    task = response.json().get("task")

    if not isinstance(task, dict):
        raise RuntimeError("Konumlu tamamlama cevabında task nesnesi yok.")

    if task.get("status") != TASK_STATUS_COMPLETED:
        raise RuntimeError(
            "Konumlu tamamlama sonrası status hatalı. "
            f"Gelen: {task.get('status')}"
        )

    print("[OK] Konum bilgisiyle görev tamamlandı.")


def approve_with_owner(
    *,
    owner: User,
    task_id: int,
) -> None:
    """Approve task through API as owner."""

    set_current_user_override(owner)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/approve",
        json={
            "note": "Konum bilgisi kontrol edildi, görev onaylandı.",
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Görev onaylama endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    task = response.json().get("task")

    if not isinstance(task, dict):
        raise RuntimeError("Görev onaylama cevabında task nesnesi yok.")

    if task.get("status") != TASK_STATUS_APPROVED:
        raise RuntimeError(
            "Görev onaylama sonrası status hatalı. "
            f"Gelen: {task.get('status')}"
        )

    print("[OK] Owner görevi onayladı.")


def assert_expected_events_exist(
    db,
    *,
    task_id: int,
) -> None:
    """Validate expected task events exist."""

    db.expire_all()

    events = (
        db.execute(
            select(TaskEvent).where(TaskEvent.task_id == task_id)
        )
        .scalars()
        .all()
    )

    event_types = {event.event_type for event in events}
    missing_event_types = EXPECTED_EVENT_TYPES - event_types

    if missing_event_types:
        raise RuntimeError(
            "Beklenen event kayıtlarının tamamı oluşmadı. "
            f"Eksik event türleri: {sorted(missing_event_types)}"
        )

    print("[OK] Görev geçmişindeki beklenen event kayıtları doğrulandı.")


def assert_location_events_exist(
    db,
    *,
    task_id: int,
) -> None:
    """Validate start and complete events contain location values."""

    db.expire_all()

    start_event = (
        db.execute(
            select(TaskEvent).where(
                TaskEvent.task_id == task_id,
                TaskEvent.event_type == "task_started",
            )
        )
        .scalars()
        .first()
    )

    if start_event is None:
        raise RuntimeError("task_started eventi bulunamadı.")

    if start_event.latitude is None or start_event.longitude is None:
        raise RuntimeError("task_started eventinde konum bilgisi yok.")

    if round(float(start_event.latitude), 4) != round(START_LATITUDE, 4):
        raise RuntimeError(
            "task_started latitude hatalı. "
            f"Beklenen: {START_LATITUDE}, Gelen: {start_event.latitude}"
        )

    if round(float(start_event.longitude), 4) != round(START_LONGITUDE, 4):
        raise RuntimeError(
            "task_started longitude hatalı. "
            f"Beklenen: {START_LONGITUDE}, Gelen: {start_event.longitude}"
        )

    complete_event = (
        db.execute(
            select(TaskEvent).where(
                TaskEvent.task_id == task_id,
                TaskEvent.event_type == "task_completed",
            )
        )
        .scalars()
        .first()
    )

    if complete_event is None:
        raise RuntimeError("task_completed eventi bulunamadı.")

    if complete_event.latitude is None or complete_event.longitude is None:
        raise RuntimeError("task_completed eventinde konum bilgisi yok.")

    if round(float(complete_event.latitude), 4) != round(COMPLETE_LATITUDE, 4):
        raise RuntimeError(
            "task_completed latitude hatalı. "
            f"Beklenen: {COMPLETE_LATITUDE}, Gelen: {complete_event.latitude}"
        )

    if round(float(complete_event.longitude), 4) != round(COMPLETE_LONGITUDE, 4):
        raise RuntimeError(
            "task_completed longitude hatalı. "
            f"Beklenen: {COMPLETE_LONGITUDE}, Gelen: {complete_event.longitude}"
        )

    print("[OK] Başlatma ve tamamlama eventlerinde konum bilgisi doğrulandı.")


def main() -> None:
    """Check location required task flow."""

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

        task = create_location_required_task(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        print("[INFO] Konum zorunlu görev akışı başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev: id={task.id} | title={task.title}")
        print(f"[INFO] Personel: {staff.username} ({staff.role})")
        print(f"[INFO] Owner: {owner.username} ({owner.role})")

        try_start_without_location_should_fail(
            staff=staff,
            task_id=task.id,
        )

        try_complete_without_location_should_fail(
            staff=staff,
            task_id=task.id,
        )

        start_with_location(
            staff=staff,
            task_id=task.id,
        )

        assert_task_status(
            db,
            task_id=task.id,
            expected_status=TASK_STATUS_IN_PROGRESS,
            label="Konumlu başlatma sonrası DB kontrol",
        )

        try_complete_without_location_should_fail(
            staff=staff,
            task_id=task.id,
        )

        assert_task_status(
            db,
            task_id=task.id,
            expected_status=TASK_STATUS_IN_PROGRESS,
            label="Konumsuz tamamlama sonrası DB kontrol",
        )

        complete_with_location(
            staff=staff,
            task_id=task.id,
        )

        assert_task_status(
            db,
            task_id=task.id,
            expected_status=TASK_STATUS_COMPLETED,
            label="Konumlu tamamlama sonrası DB kontrol",
        )

        approve_with_owner(
            owner=owner,
            task_id=task.id,
        )

        assert_task_status(
            db,
            task_id=task.id,
            expected_status=TASK_STATUS_APPROVED,
            label="Onay sonrası DB kontrol",
        )

        assert_expected_events_exist(
            db,
            task_id=task.id,
        )

        assert_location_events_exist(
            db,
            task_id=task.id,
        )

        print("")
        print("[OK] Konum zorunlu görev akışı başarılı.")
    finally:
        db.close()
        app.dependency_overrides.clear()


if __name__ == "__main__":
    main()