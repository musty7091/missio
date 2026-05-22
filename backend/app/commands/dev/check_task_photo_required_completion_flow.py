from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
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
OWNER_USERNAME = "patron"
STAFF_USERNAME = "ahmet"

TASK_TITLE_PHOTO_REQUIRED_FLOW = "PHOTO REQUIRED DEMO - Fotoğraf zorunlu tamamlama akışı"

EXPECTED_EVENT_TYPES = {
    "extra_task_created",
    "task_started",
    "task_attachment_uploaded",
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
    """Delete old photo required demo data."""

    old_tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title == TASK_TITLE_PHOTO_REQUIRED_FLOW,
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


def create_photo_required_task(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> Task:
    """Create fresh photo required demo task."""

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=staff,
        title=TASK_TITLE_PHOTO_REQUIRED_FLOW,
        description="Fotoğraf zorunlu görev tamamlama kuralı için demo görev.",
        requires_photo=True,
        requires_location=False,
        requires_manager_approval=True,
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_photo_required_completion_flow",
    )

    db.commit()
    db.refresh(task)

    return task


def create_demo_jpeg_bytes() -> bytes:
    """Create in-memory demo JPEG image."""

    image = Image.new("RGB", (2400, 1800), (238, 238, 238))

    for x in range(100, 2300, 160):
        for y in range(100, 1700, 160):
            for dx in range(80):
                for dy in range(80):
                    image.putpixel((x + dx, y + dy), (175, 175, 175))

    output = BytesIO()
    image.save(output, format="JPEG", quality=95)

    return output.getvalue()


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


def start_task_with_staff(
    *,
    staff: User,
    task_id: int,
) -> None:
    """Start task through API as assigned staff."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/start",
        json={
            "note": "Personel fotoğraf zorunlu göreve başladı.",
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Görev başlatma endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()
    task = response_json.get("task")

    if not isinstance(task, dict):
        raise RuntimeError("Görev başlatma cevabında task nesnesi yok.")

    if task.get("status") != TASK_STATUS_IN_PROGRESS:
        raise RuntimeError(
            "Görev başlatma sonrası status hatalı. "
            f"Gelen: {task.get('status')}"
        )

    print("[OK] Personel görevi başlattı.")


def try_complete_without_photo_should_fail(
    *,
    staff: User,
    task_id: int,
) -> None:
    """Try to complete task without photo and expect failure."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={
            "note": "Fotoğraf olmadan tamamlamaya çalışıyorum.",
        },
    )

    if response.status_code != 400:
        raise RuntimeError(
            "Fotoğrafsız tamamlama başarısız olmalıydı ama beklenen hata gelmedi. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()
    detail = str(response_json.get("detail", ""))

    if "fotoğraf" not in detail.lower() and "ek" not in detail.lower():
        raise RuntimeError(
            "Fotoğrafsız tamamlama hatası beklenen açıklamayı içermiyor. "
            f"detail={detail}"
        )

    print("[OK] Fotoğraf yokken görev tamamlanamadı.")


def upload_photo_with_staff(
    *,
    staff: User,
    task_id: int,
    image_content: bytes,
) -> int:
    """Upload proof photo through API as assigned staff."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/attachments",
        files={
            "file": (
                "iphone-proof-photo.jpg",
                image_content,
                "image/jpeg",
            )
        },
        data={
            "latitude": "36.8000",
            "longitude": "34.6333",
            "location_accuracy": "22",
        },
    )

    if response.status_code != 201:
        raise RuntimeError(
            "Fotoğraf yükleme endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()
    attachment = response_json.get("attachment")

    if not isinstance(attachment, dict):
        raise RuntimeError("Fotoğraf yükleme cevabında attachment nesnesi yok.")

    attachment_id = attachment.get("id")

    if not isinstance(attachment_id, int):
        raise RuntimeError("Fotoğraf yükleme cevabında attachment id geçersiz.")

    if attachment.get("file_type") != "image/jpeg":
        raise RuntimeError(
            "Yüklenen fotoğraf image/jpeg olarak dönmedi. "
            f"file_type={attachment.get('file_type')}"
        )

    print(
        "[OK] Personel fotoğraf kanıtı yükledi. "
        f"attachment_id={attachment_id}, file_size={attachment.get('file_size')}"
    )

    return attachment_id


def complete_task_with_staff(
    *,
    staff: User,
    task_id: int,
) -> None:
    """Complete task through API as assigned staff."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={
            "note": "Fotoğraf yüklendi, görev tamamlandı.",
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Fotoğraf sonrası görev tamamlama endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()
    task = response_json.get("task")

    if not isinstance(task, dict):
        raise RuntimeError("Görev tamamlama cevabında task nesnesi yok.")

    if task.get("status") != TASK_STATUS_COMPLETED:
        raise RuntimeError(
            "Görev tamamlama sonrası status hatalı. "
            f"Gelen: {task.get('status')}"
        )

    print("[OK] Fotoğraf yüklendikten sonra görev tamamlandı.")


def approve_task_with_owner(
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
            "note": "Fotoğraf kanıtı kontrol edildi, görev onaylandı.",
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Görev onaylama endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()
    task = response_json.get("task")

    if not isinstance(task, dict):
        raise RuntimeError("Görev onaylama cevabında task nesnesi yok.")

    if task.get("status") != TASK_STATUS_APPROVED:
        raise RuntimeError(
            "Görev onaylama sonrası status hatalı. "
            f"Gelen: {task.get('status')}"
        )

    print("[OK] Owner görevi onayladı.")


def assert_attachment_exists(
    db,
    *,
    attachment_id: int,
) -> None:
    """Validate attachment record and physical file exist."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is None:
        raise RuntimeError("Fotoğraf kaydı veritabanında bulunamadı.")

    file_path = Path(attachment.file_path)

    if not file_path.exists() or not file_path.is_file():
        raise RuntimeError(
            "Fotoğraf fiziksel storage klasöründe bulunamadı. "
            f"file_path={attachment.file_path}"
        )

    if attachment.file_size is None or attachment.file_size <= 0:
        raise RuntimeError("Fotoğraf dosya boyutu geçersiz.")

    print("[OK] Fotoğraf kaydı ve fiziksel dosya doğrulandı.")


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


def main() -> None:
    """Check photo required task completion flow."""

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

        task = create_photo_required_task(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        print("[INFO] Fotoğraf zorunlu görev tamamlama akışı başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev: id={task.id} | title={task.title}")
        print(f"[INFO] Personel: {staff.username} ({staff.role})")
        print(f"[INFO] Owner: {owner.username} ({owner.role})")

        start_task_with_staff(
            staff=staff,
            task_id=task.id,
        )

        assert_task_status(
            db,
            task_id=task.id,
            expected_status=TASK_STATUS_IN_PROGRESS,
            label="Başlatma sonrası DB kontrol",
        )

        try_complete_without_photo_should_fail(
            staff=staff,
            task_id=task.id,
        )

        assert_task_status(
            db,
            task_id=task.id,
            expected_status=TASK_STATUS_IN_PROGRESS,
            label="Fotoğrafsız tamamlama sonrası DB kontrol",
        )

        image_content = create_demo_jpeg_bytes()

        attachment_id = upload_photo_with_staff(
            staff=staff,
            task_id=task.id,
            image_content=image_content,
        )

        assert_attachment_exists(
            db,
            attachment_id=attachment_id,
        )

        complete_task_with_staff(
            staff=staff,
            task_id=task.id,
        )

        assert_task_status(
            db,
            task_id=task.id,
            expected_status=TASK_STATUS_COMPLETED,
            label="Fotoğraflı tamamlama sonrası DB kontrol",
        )

        approve_task_with_owner(
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

        print("")
        print("[OK] Fotoğraf zorunlu görev tamamlama akışı başarılı.")
    finally:
        db.close()
        app.dependency_overrides.clear()


if __name__ == "__main__":
    main()