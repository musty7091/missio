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

TASK_TITLE_ATTACHMENT_FILE_FLOW = "ATTACHMENT DEMO - Fotoğraf görüntüleme akışı"


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
    """Delete old attachment file endpoint demo data."""

    old_tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title == TASK_TITLE_ATTACHMENT_FILE_FLOW,
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


def create_demo_task(
    db,
    *,
    owner: User,
    business: Business,
    staff: User,
) -> Task:
    """Create fresh demo task."""

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=staff,
        title=TASK_TITLE_ATTACHMENT_FILE_FLOW,
        description="Fotoğraf görüntüleme endpoint akışı için oluşturulan demo görev.",
        requires_photo=True,
        requires_location=False,
        requires_manager_approval=True,
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_attachment_file_endpoint_flow",
    )

    db.commit()
    db.refresh(task)

    return task


def create_demo_jpeg_bytes() -> bytes:
    """Create in-memory demo JPEG image."""

    image = Image.new("RGB", (2200, 1600), (245, 245, 245))

    for x in range(100, 2100, 180):
        for y in range(100, 1500, 180):
            for dx in range(90):
                for dy in range(90):
                    image.putpixel((x + dx, y + dy), (170, 170, 170))

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
                "iphone-camera-proof.jpg",
                image_content,
                "image/jpeg",
            )
        },
        data={
            "latitude": "36.8000",
            "longitude": "34.6333",
            "location_accuracy": "20",
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

    attachment_id = attachment.get("id")

    if not isinstance(attachment_id, int):
        raise RuntimeError("Upload cevabında attachment id geçersiz.")

    print(
        "[OK] Fotoğraf yüklendi. "
        f"attachment_id={attachment_id}, file_size={attachment.get('file_size')}"
    )

    return attachment


def assert_file_response_is_valid_jpeg(
    *,
    response_content: bytes,
    content_type: str,
    label: str,
) -> None:
    """Validate file endpoint response content."""

    normalized_content_type = content_type.lower()

    if "image/jpeg" not in normalized_content_type:
        raise RuntimeError(
            f"{label} dosya endpointi image/jpeg döndürmedi. "
            f"content_type={content_type}"
        )

    if len(response_content) <= 0:
        raise RuntimeError(f"{label} dosya endpointi boş içerik döndürdü.")

    if not response_content.startswith(b"\xff\xd8"):
        raise RuntimeError(f"{label} dosya içeriği JPEG başlangıcı taşımıyor.")

    if not response_content.endswith(b"\xff\xd9"):
        raise RuntimeError(f"{label} dosya içeriği JPEG bitişi taşımıyor.")


def get_attachment_file_with_user(
    *,
    user: User,
    task_id: int,
    attachment_id: int,
    label: str,
) -> None:
    """Download attachment file through API."""

    set_current_user_override(user)

    client = TestClient(app)

    response = client.get(
        f"/api/v1/tasks/{task_id}/attachments/{attachment_id}/file"
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"{label} fotoğraf görüntüleme endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    content_type = response.headers.get("content-type", "")

    assert_file_response_is_valid_jpeg(
        response_content=response.content,
        content_type=content_type,
        label=label,
    )

    print(
        f"[OK] {label} fotoğraf görüntüleme endpointi başarılı. "
        f"size={len(response.content)} bytes"
    )


def delete_attachment_with_staff(
    *,
    staff: User,
    task_id: int,
    attachment_id: int,
) -> None:
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

    print(f"[OK] Test fotoğrafı silindi. attachment_id={attachment_id}")


def assert_attachment_file_exists(
    db,
    *,
    attachment_id: int,
) -> str:
    """Validate attachment file exists and return file path."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is None:
        raise RuntimeError("Yüklenen fotoğraf veritabanında bulunamadı.")

    if attachment.file_type != "image/jpeg":
        raise RuntimeError(
            "Fotoğraf image/jpeg olarak kaydedilmedi. "
            f"file_type={attachment.file_type}"
        )

    file_path = attachment.file_path
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise RuntimeError(
            "Fotoğraf fiziksel storage klasöründe bulunamadı. "
            f"file_path={file_path}"
        )

    return file_path


def assert_attachment_deleted(
    db,
    *,
    attachment_id: int,
    previous_file_path: str,
) -> None:
    """Validate attachment record and file are deleted."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is not None:
        raise RuntimeError("Silinen fotoğraf kaydı veritabanında hala duruyor.")

    path = Path(previous_file_path)

    if path.exists():
        raise RuntimeError("Silinen fotoğraf dosyası storage klasöründe hala duruyor.")

    print("[OK] Test fotoğrafı veritabanı ve storage üzerinden temizlendi.")


def main() -> None:
    """Check task attachment file endpoint flow."""

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

        task = create_demo_task(
            db=db,
            owner=owner,
            business=business,
            staff=staff,
        )

        print("[INFO] Görev fotoğraf görüntüleme endpoint kontrolü başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev: id={task.id} | title={task.title}")
        print(f"[INFO] Personel: {staff.username} ({staff.role})")

        image_content = create_demo_jpeg_bytes()

        uploaded_attachment = upload_attachment_with_staff(
            staff=staff,
            task_id=task.id,
            image_content=image_content,
        )

        attachment_id = int(uploaded_attachment["id"])

        previous_file_path = assert_attachment_file_exists(
            db,
            attachment_id=attachment_id,
        )

        get_attachment_file_with_user(
            user=staff,
            task_id=task.id,
            attachment_id=attachment_id,
            label="Atanan personel",
        )

        get_attachment_file_with_user(
            user=owner,
            task_id=task.id,
            attachment_id=attachment_id,
            label="Owner",
        )

        delete_attachment_with_staff(
            staff=staff,
            task_id=task.id,
            attachment_id=attachment_id,
        )

        assert_attachment_deleted(
            db,
            attachment_id=attachment_id,
            previous_file_path=previous_file_path,
        )

        print("")
        print("[OK] Görev fotoğraf görüntüleme endpoint akışı başarılı.")
    finally:
        db.close()
        app.dependency_overrides.clear()


if __name__ == "__main__":
    main()
