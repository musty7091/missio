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
from app.services.task_service import create_extra_task


BUSINESS_SLUG = "missio-demo-market"
OWNER_USERNAME = "patron"
STAFF_USERNAME = "ahmet"

TASK_TITLE_ATTACHMENT_FLOW = "ATTACHMENT DEMO - Fotoğraf yükleme akışı"

EXPECTED_UPLOAD_EVENT_TYPE = "task_attachment_uploaded"
EXPECTED_DELETE_EVENT_TYPE = "task_attachment_deleted"


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
    """Delete old demo file if it exists under storage directory."""

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


def cleanup_old_attachment_demo_data(db, *, business_id: int) -> None:
    """Delete old attachment demo data."""

    old_tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title == TASK_TITLE_ATTACHMENT_FLOW,
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


def create_demo_attachment_task(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> Task:
    """Create fresh demo task for attachment endpoint flow."""

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=staff,
        title=TASK_TITLE_ATTACHMENT_FLOW,
        description="Fotoğraf yükleme endpoint akışı için oluşturulan demo görev.",
        requires_photo=True,
        requires_location=False,
        requires_manager_approval=True,
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_attachment_endpoint_flow",
    )

    db.commit()
    db.refresh(task)

    return task


def create_demo_jpeg_bytes() -> bytes:
    """Create in-memory demo JPEG image."""

    image = Image.new("RGB", (2400, 1800), (235, 235, 235))

    for x in range(0, 2400, 120):
        for y in range(0, 1800, 120):
            if (x // 120 + y // 120) % 2 == 0:
                for dx in range(80):
                    for dy in range(80):
                        image.putpixel((x + dx, y + dy), (190, 190, 190))

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


def upload_attachment_with_staff(
    *,
    staff: User,
    task_id: int,
    image_content: bytes,
) -> dict:
    """Upload attachment through API as assigned staff."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.post(
        f"/api/v1/tasks/{task_id}/attachments",
        files={
            "file": (
                "iphone-demo-photo.jpg",
                image_content,
                "image/jpeg",
            )
        },
        data={
            "latitude": "36.8000",
            "longitude": "34.6333",
            "location_accuracy": "25",
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
        raise RuntimeError("Upload cevabında attachment nesnesi yok.")

    print(
        "[OK] Fotoğraf yükleme endpointi başarılı. "
        f"attachment_id={attachment.get('id')}, "
        f"file_size={attachment.get('file_size')}"
    )

    return attachment


def list_attachments_with_user(
    *,
    user: User,
    task_id: int,
    label: str,
) -> dict:
    """List attachments through API."""

    set_current_user_override(user)

    client = TestClient(app)

    response = client.get(f"/api/v1/tasks/{task_id}/attachments")

    if response.status_code != 200:
        raise RuntimeError(
            f"{label} fotoğraf listeleme endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()

    if not isinstance(response_json.get("attachments"), list):
        raise RuntimeError(f"{label} listeleme cevabında attachments liste değil.")

    if response_json.get("total_count", 0) < 1:
        raise RuntimeError(f"{label} listeleme cevabında fotoğraf bulunamadı.")

    print(
        f"[OK] {label} fotoğraf listeleme endpointi başarılı. "
        f"total_count={response_json.get('total_count')}"
    )

    return response_json


def list_events_with_user(
    *,
    user: User,
    task_id: int,
    label: str,
) -> dict:
    """List task events through API."""

    set_current_user_override(user)

    client = TestClient(app)

    response = client.get(f"/api/v1/tasks/{task_id}/events")

    if response.status_code != 200:
        raise RuntimeError(
            f"{label} görev event endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()
    events = response_json.get("events")

    if not isinstance(events, list):
        raise RuntimeError(f"{label} event cevabında events liste değil.")

    event_types = {
        event.get("event_type")
        for event in events
        if isinstance(event, dict)
    }

    if EXPECTED_UPLOAD_EVENT_TYPE not in event_types:
        raise RuntimeError(
            f"{label} event listesinde {EXPECTED_UPLOAD_EVENT_TYPE} bulunamadı."
        )

    print(
        f"[OK] {label} görev geçmişinde fotoğraf yükleme eventi görüldü."
    )

    return response_json


def delete_attachment_with_staff(
    *,
    staff: User,
    task_id: int,
    attachment_id: int,
) -> dict:
    """Delete attachment through API as assigned staff."""

    set_current_user_override(staff)

    client = TestClient(app)

    response = client.delete(
        f"/api/v1/tasks/{task_id}/attachments/{attachment_id}"
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Fotoğraf silme endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    response_json = response.json()

    if response_json.get("attachment_id") != attachment_id:
        raise RuntimeError("Silme cevabındaki attachment_id beklenen değer değil.")

    print(f"[OK] Fotoğraf silme endpointi başarılı. attachment_id={attachment_id}")

    return response_json


def assert_uploaded_attachment_record(
    db,
    *,
    attachment_id: int,
    task_id: int,
) -> TaskAttachment:
    """Validate uploaded attachment database record and physical file."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is None:
        raise RuntimeError("Yüklenen fotoğraf veritabanında bulunamadı.")

    if attachment.task_id != task_id:
        raise RuntimeError("Fotoğraf yanlış task_id ile kaydedildi.")

    if attachment.file_type != "image/jpeg":
        raise RuntimeError(
            "Fotoğraf JPEG olarak kaydedilmedi. "
            f"Gelen file_type={attachment.file_type}"
        )

    if not attachment.file_name.lower().endswith(".jpg"):
        raise RuntimeError(
            "Fotoğraf dosya adı .jpg ile bitmiyor. "
            f"file_name={attachment.file_name}"
        )

    if attachment.file_size is None or attachment.file_size <= 0:
        raise RuntimeError("Fotoğraf dosya boyutu geçersiz.")

    if attachment.file_size > 3 * 1024 * 1024:
        raise RuntimeError("Optimize edilmiş fotoğraf 3 MB sınırını aştı.")

    physical_path = Path(attachment.file_path)

    if not physical_path.exists() or not physical_path.is_file():
        raise RuntimeError(
            "Fotoğraf fiziksel storage klasöründe bulunamadı. "
            f"file_path={attachment.file_path}"
        )

    print(
        "[OK] Fotoğraf veritabanı ve storage kaydı doğrulandı. "
        f"path={attachment.file_path}"
    )

    return attachment


def assert_deleted_attachment_record(
    db,
    *,
    attachment_id: int,
    previous_file_path: str,
) -> None:
    """Validate attachment record and physical file are deleted."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is not None:
        raise RuntimeError("Silinen fotoğraf kaydı veritabanında hâlâ duruyor.")

    physical_path = Path(previous_file_path)

    if physical_path.exists():
        raise RuntimeError("Silinen fotoğraf fiziksel storage klasöründe hâlâ duruyor.")

    print("[OK] Fotoğraf veritabanı kaydı ve fiziksel dosya silindi.")


def assert_delete_event_exists(db, *, task_id: int) -> None:
    """Validate delete event exists."""

    db.expire_all()

    events = (
        db.execute(
            select(TaskEvent).where(TaskEvent.task_id == task_id)
        )
        .scalars()
        .all()
    )

    event_types = {event.event_type for event in events}

    if EXPECTED_DELETE_EVENT_TYPE not in event_types:
        raise RuntimeError(
            f"Görev geçmişinde {EXPECTED_DELETE_EVENT_TYPE} eventi bulunamadı."
        )

    print("[OK] Görev geçmişinde fotoğraf silme eventi doğrulandı.")


def main() -> None:
    """Check task attachment endpoint flow."""

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

        cleanup_old_attachment_demo_data(db, business_id=business.id)

        task = create_demo_attachment_task(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        print("[INFO] Görev fotoğraf endpoint akışı kontrolü başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev: id={task.id} | title={task.title}")
        print(f"[INFO] Personel: {staff.username} ({staff.role})")

        image_content = create_demo_jpeg_bytes()

        print(f"[INFO] Demo görsel üretildi. size={len(image_content)} bytes")

        uploaded_attachment_response = upload_attachment_with_staff(
            staff=staff,
            task_id=task.id,
            image_content=image_content,
        )

        attachment_id = int(uploaded_attachment_response["id"])

        attachment = assert_uploaded_attachment_record(
            db,
            attachment_id=attachment_id,
            task_id=task.id,
        )

        previous_file_path = attachment.file_path

        list_attachments_with_user(
            user=staff,
            task_id=task.id,
            label="Atanan personel",
        )

        list_attachments_with_user(
            user=owner,
            task_id=task.id,
            label="Owner",
        )

        list_events_with_user(
            user=staff,
            task_id=task.id,
            label="Atanan personel",
        )

        delete_attachment_with_staff(
            staff=staff,
            task_id=task.id,
            attachment_id=attachment_id,
        )

        assert_deleted_attachment_record(
            db,
            attachment_id=attachment_id,
            previous_file_path=previous_file_path,
        )

        assert_delete_event_exists(db, task_id=task.id)

        print("")
        print("[OK] Görev fotoğraf yükleme/listeleme/silme endpoint akışı başarılı.")
    finally:
        db.close()
        app.dependency_overrides.clear()


if __name__ == "__main__":
    main()