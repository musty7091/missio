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
from app.services.task_attachment_service import delete_physical_attachment_file
from app.services.task_service import create_extra_task


BUSINESS_SLUG = "missio-demo-market"
OWNER_USERNAME = "owner"
ASSIGNED_STAFF_USERNAME = "ahmet"
OTHER_STAFF_USERNAME = "ali"

TASK_TITLE_ACCESS_CONTROL_FLOW = "SECURITY CHECK - Görev fotoğraf yetki kontrolü"


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
    """Delete demo attachment file safely."""

    if not file_path:
        return

    try:
        delete_physical_attachment_file(file_path)
    except Exception as exc:
        print(f"[WARN] Demo dosyası temizlenemedi: {file_path} | {exc}")


def cleanup_old_demo_data(db, *, business_id: int) -> None:
    """Delete old access-control demo data."""

    old_tasks = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.title == TASK_TITLE_ACCESS_CONTROL_FLOW,
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
    assigned_staff: User,
) -> Task:
    """Create fresh demo task assigned to selected staff."""

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=assigned_staff,
        title=TASK_TITLE_ACCESS_CONTROL_FLOW,
        description="Görev fotoğraf yetki kontrolü için oluşturulan demo görev.",
        requires_photo=True,
        requires_location=False,
        requires_manager_approval=True,
        ip_address="127.0.0.1",
        user_agent="Missio command check_task_attachment_access_control_flow",
    )

    db.commit()
    db.refresh(task)

    return task


def create_demo_jpeg_bytes() -> bytes:
    """Create in-memory demo JPEG image."""

    image = Image.new("RGB", (900, 600), (245, 245, 245))

    for x in range(80, 820, 120):
        for y in range(80, 520, 120):
            for dx in range(50):
                for dy in range(50):
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


def build_client_for_user(user: User) -> TestClient:
    """Build TestClient with selected current user."""

    set_current_user_override(user)

    return TestClient(app)


def upload_attachment_with_assigned_staff(
    *,
    assigned_staff: User,
    task_id: int,
    image_content: bytes,
) -> dict:
    """Upload attachment through API as assigned staff."""

    client = build_client_for_user(assigned_staff)

    response = client.post(
        f"/api/v1/tasks/{task_id}/attachments",
        files={
            "file": (
                "assigned-staff-proof.jpg",
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
            "Atanan personel fotoğraf yükleme endpointi başarısız. "
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
        "[OK] Atanan personel fotoğraf yükleyebildi. "
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


def get_attachment_file_with_allowed_user(
    *,
    user: User,
    task_id: int,
    attachment_id: int,
    label: str,
) -> None:
    """Download attachment file through API with allowed user."""

    client = build_client_for_user(user)

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


def assert_forbidden_response(
    *,
    user: User,
    method: str,
    url: str,
    label: str,
) -> None:
    """Assert selected user receives HTTP 403 for forbidden operation."""

    client = build_client_for_user(user)

    normalized_method = method.strip().upper()

    if normalized_method == "GET":
        response = client.get(url)
    elif normalized_method == "DELETE":
        response = client.delete(url)
    else:
        raise RuntimeError(f"Desteklenmeyen test metodu: {method}")

    if response.status_code != 403:
        raise RuntimeError(
            f"{label} için beklenen HTTP 403 idi ancak HTTP {response.status_code} döndü. "
            f"Response: {response.text}"
        )

    print(f"[OK] {label} doğru şekilde reddedildi. HTTP 403")


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


def assert_attachment_still_exists(
    db,
    *,
    attachment_id: int,
    previous_file_path: str,
) -> None:
    """Validate forbidden delete did not remove attachment."""

    db.expire_all()

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is None:
        raise RuntimeError(
            "Yetkisiz silme denemesinden sonra fotoğraf kaydı kayboldu."
        )

    path = Path(previous_file_path)

    if not path.exists() or not path.is_file():
        raise RuntimeError(
            "Yetkisiz silme denemesinden sonra fiziksel fotoğraf dosyası kayboldu."
        )

    print("[OK] Yetkisiz silme denemesi fotoğraf kaydını ve dosyasını etkilemedi.")


def delete_attachment_with_assigned_staff(
    *,
    assigned_staff: User,
    task_id: int,
    attachment_id: int,
) -> None:
    """Delete attachment through API as assigned staff."""

    client = build_client_for_user(assigned_staff)

    response = client.delete(
        f"/api/v1/tasks/{task_id}/attachments/{attachment_id}"
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Atanan personel fotoğraf silme endpointi başarısız. "
            f"HTTP {response.status_code}: {response.text}"
        )

    print(f"[OK] Test fotoğrafı atanan personel tarafından silindi. attachment_id={attachment_id}")


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
        raise RuntimeError("Silinen fotoğraf kaydı veritabanında hâlâ duruyor.")

    path = Path(previous_file_path)

    if path.exists():
        raise RuntimeError("Silinen fotoğraf dosyası storage klasöründe hâlâ duruyor.")

    print("[OK] Test fotoğrafı veritabanı ve storage üzerinden temizlendi.")


def main() -> None:
    """Check task attachment access control flow."""

    db = SessionLocal()
    business_id: int | None = None

    try:
        business = get_demo_business(db)
        business_id = business.id

        owner = get_demo_user(
            db=db,
            business_id=business.id,
            username=OWNER_USERNAME,
        )
        assigned_staff = get_demo_user(
            db=db,
            business_id=business.id,
            username=ASSIGNED_STAFF_USERNAME,
        )
        other_staff = get_demo_user(
            db=db,
            business_id=business.id,
            username=OTHER_STAFF_USERNAME,
        )

        cleanup_old_demo_data(db, business_id=business.id)

        task = create_demo_task(
            db=db,
            owner=owner,
            business=business,
            assigned_staff=assigned_staff,
        )

        print("[INFO] Görev fotoğraf yetki kontrolü başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev: id={task.id} | title={task.title}")
        print(f"[INFO] Atanan personel: {assigned_staff.username} ({assigned_staff.role})")
        print(f"[INFO] Diğer personel: {other_staff.username} ({other_staff.role})")

        image_content = create_demo_jpeg_bytes()

        uploaded_attachment = upload_attachment_with_assigned_staff(
            assigned_staff=assigned_staff,
            task_id=task.id,
            image_content=image_content,
        )

        attachment_id = int(uploaded_attachment["id"])

        previous_file_path = assert_attachment_file_exists(
            db,
            attachment_id=attachment_id,
        )

        get_attachment_file_with_allowed_user(
            user=assigned_staff,
            task_id=task.id,
            attachment_id=attachment_id,
            label="Atanan personel",
        )

        get_attachment_file_with_allowed_user(
            user=owner,
            task_id=task.id,
            attachment_id=attachment_id,
            label="Owner",
        )

        assert_forbidden_response(
            user=other_staff,
            method="GET",
            url=f"/api/v1/tasks/{task.id}/attachments",
            label="Diğer personelin attachment listeleme denemesi",
        )

        assert_forbidden_response(
            user=other_staff,
            method="GET",
            url=f"/api/v1/tasks/{task.id}/attachments/{attachment_id}/file",
            label="Diğer personelin fotoğraf görüntüleme denemesi",
        )

        assert_forbidden_response(
            user=other_staff,
            method="DELETE",
            url=f"/api/v1/tasks/{task.id}/attachments/{attachment_id}",
            label="Diğer personelin fotoğraf silme denemesi",
        )

        assert_attachment_still_exists(
            db,
            attachment_id=attachment_id,
            previous_file_path=previous_file_path,
        )

        delete_attachment_with_assigned_staff(
            assigned_staff=assigned_staff,
            task_id=task.id,
            attachment_id=attachment_id,
        )

        assert_attachment_deleted(
            db,
            attachment_id=attachment_id,
            previous_file_path=previous_file_path,
        )

        cleanup_old_demo_data(db, business_id=business.id)

        print("")
        print("[OK] Görev fotoğraf yetki kontrolü başarılı.")
    finally:
        app.dependency_overrides.clear()

        try:
            db.rollback()

            if business_id is not None:
                cleanup_old_demo_data(db, business_id=business_id)
        except Exception as cleanup_exc:
            print(f"[WARN] Test sonrası temizlik sırasında hata oluştu: {cleanup_exc}")
        finally:
            db.close()


if __name__ == "__main__":
    main()
