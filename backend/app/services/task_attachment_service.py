from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.models.user import User
from app.schemas.task import (
    TASK_ATTACHMENT_TYPE_EVIDENCE,
    TASK_ATTACHMENT_TYPE_REFERENCE,
    TASK_STATUS_APPROVED,
    TASK_STATUS_CANCELLED,
    validate_task_attachment_type_value,
)
from app.services.task_service import (
    TaskNotFoundError,
    TaskPermissionError,
    TaskServiceError,
    create_task_event,
    ensure_can_view_task,
)


register_heif_opener()


MAX_UPLOAD_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_STORED_FILE_SIZE_BYTES = 3 * 1024 * 1024
MAX_ATTACHMENTS_PER_TASK = 3
MAX_IMAGE_LONG_EDGE_PX = 1600
MAX_IMAGE_PIXELS = 20_000_000
JPEG_QUALITY = 75

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

TASK_ATTACHMENT_STORAGE_ROOT = Path("storage") / "task_attachments"

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
}

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "image/heif-sequence",
    "image/heic-sequence",
}

ALLOWED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
    "HEIF",
    "HEIC",
}


class TaskAttachmentServiceError(ValueError):
    """Base error for task attachment service failures."""


class TaskAttachmentNotFoundError(TaskAttachmentServiceError):
    """Raised when task attachment is not found."""


class TaskAttachmentPermissionError(TaskAttachmentServiceError):
    """Raised when current user has no permission for attachment operation."""


class TaskAttachmentFileError(TaskAttachmentServiceError):
    """Raised when uploaded file is invalid."""


class TaskAttachmentLimitError(TaskAttachmentServiceError):
    """Raised when task attachment limit is exceeded."""


@dataclass(frozen=True)
class TaskAttachmentListResult:
    """Task attachment list result."""

    attachments: list[TaskAttachment]
    total_count: int


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def normalize_file_extension(file_name: str | None) -> str:
    """Return normalized file extension."""

    if not file_name:
        return ""

    return Path(file_name).suffix.strip().lower()


def get_task_attachment_storage_root_absolute() -> Path:
    """Return absolute task attachment storage root."""

    return TASK_ATTACHMENT_STORAGE_ROOT.resolve(strict=False)


def resolve_safe_task_attachment_storage_path(file_path: str | Path) -> Path:
    """Resolve and validate a task attachment path under storage root."""

    path = Path(file_path)

    if path.is_absolute():
        raise TaskAttachmentFileError("Geçersiz dosya yolu.")

    if any(part == ".." for part in path.parts):
        raise TaskAttachmentFileError("Geçersiz dosya yolu.")

    storage_root = get_task_attachment_storage_root_absolute()
    resolved_path = path.resolve(strict=False)

    try:
        resolved_path.relative_to(storage_root)
    except ValueError as exc:
        raise TaskAttachmentFileError("Geçersiz dosya yolu.") from exc

    return resolved_path


def validate_upload_file_metadata(upload_file: UploadFile) -> None:
    """Validate upload file metadata before reading content."""

    extension = normalize_file_extension(upload_file.filename)

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise TaskAttachmentFileError(
            "Desteklenmeyen dosya türü. Sadece JPG, JPEG, PNG, WEBP, HEIC veya HEIF yüklenebilir."
        )

    content_type = (upload_file.content_type or "").strip().lower()

    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise TaskAttachmentFileError(
            "Desteklenmeyen içerik türü. Sadece görsel dosyaları yüklenebilir."
        )


def read_upload_file_content(upload_file: UploadFile) -> bytes:
    """Read upload file content with size protection."""

    upload_file.file.seek(0)
    content = upload_file.file.read(MAX_UPLOAD_FILE_SIZE_BYTES + 1)
    upload_file.file.seek(0)

    if not content:
        raise TaskAttachmentFileError("Yüklenen dosya boş.")

    if len(content) > MAX_UPLOAD_FILE_SIZE_BYTES:
        raise TaskAttachmentFileError(
            "Dosya çok büyük. Yüklenebilecek maksimum görsel boyutu 10 MB."
        )

    return content


def validate_opened_image(image: Image.Image) -> None:
    """Validate opened image format and dimensions."""

    image_format = (image.format or "").strip().upper()

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise TaskAttachmentFileError(
            "Desteklenmeyen görsel formatı. Sadece JPG, JPEG, PNG, WEBP, HEIC veya HEIF yüklenebilir."
        )

    if image.width <= 0 or image.height <= 0:
        raise TaskAttachmentFileError("Görsel ölçüleri geçersiz.")

    pixel_count = image.width * image.height

    if pixel_count > MAX_IMAGE_PIXELS:
        raise TaskAttachmentFileError(
            "Görsel çözünürlüğü çok büyük. Lütfen daha düşük çözünürlüklü bir görsel yükleyin."
        )


def open_uploaded_image(content: bytes) -> Image.Image:
    """Open uploaded image safely."""

    try:
        image = Image.open(BytesIO(content))
        validate_opened_image(image)
        image.load()
    except Image.DecompressionBombError as exc:
        raise TaskAttachmentFileError(
            "Görsel çözünürlüğü güvenli sınırın üzerinde."
        ) from exc
    except UnidentifiedImageError as exc:
        raise TaskAttachmentFileError("Yüklenen dosya geçerli bir görsel değil.") from exc
    except OSError as exc:
        raise TaskAttachmentFileError("Görsel dosyası okunamadı.") from exc

    return image


def convert_image_to_optimized_jpeg(content: bytes) -> tuple[bytes, int]:
    """Convert uploaded image to optimized JPEG bytes."""

    image = open_uploaded_image(content)
    image = ImageOps.exif_transpose(image)

    if image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")

    if image.mode == "L":
        image = image.convert("RGB")

    image.thumbnail(
        (MAX_IMAGE_LONG_EDGE_PX, MAX_IMAGE_LONG_EDGE_PX),
        Image.Resampling.LANCZOS,
    )

    quality_candidates = [JPEG_QUALITY, 70, 65, 60, 55, 50]
    edge_candidates = [MAX_IMAGE_LONG_EDGE_PX, 1400, 1200, 1000]

    for edge in edge_candidates:
        working_image = image.copy()
        working_image.thumbnail((edge, edge), Image.Resampling.LANCZOS)

        for quality in quality_candidates:
            output = BytesIO()
            working_image.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            optimized_content = output.getvalue()

            if len(optimized_content) <= MAX_STORED_FILE_SIZE_BYTES:
                return optimized_content, len(optimized_content)

    raise TaskAttachmentFileError(
        "Görsel optimize edildikten sonra bile çok büyük kaldı. Lütfen daha küçük bir görsel yükleyin."
    )


def get_attachment_storage_directory(task: Task) -> Path:
    """Return storage directory for task attachments."""

    task_date = task.task_date
    year_value = str(task_date.year)
    month_value = str(task_date.month).zfill(2)

    return (
        TASK_ATTACHMENT_STORAGE_ROOT
        / f"business_{task.business_id}"
        / year_value
        / month_value
        / f"task_{task.id}"
    )


def build_safe_storage_path(task: Task) -> tuple[Path, str]:
    """Build safe physical and relative storage path."""

    storage_directory = get_attachment_storage_directory(task)
    safe_file_name = f"{uuid4()}.jpg"
    physical_path = storage_directory / safe_file_name
    safe_physical_path = resolve_safe_task_attachment_storage_path(physical_path)
    relative_path = physical_path.as_posix()

    return safe_physical_path, relative_path


def count_active_task_attachments(
    db: Session,
    *,
    task_id: int,
    attachment_type: str | None = None,
) -> int:
    """Return active attachment count for task."""

    query = select(func.count(TaskAttachment.id)).where(TaskAttachment.task_id == task_id)

    if attachment_type is not None:
        query = query.where(TaskAttachment.attachment_type == attachment_type)

    return int(db.execute(query).scalar_one())


def ensure_task_allows_attachment_upload(
    db: Session,
    *,
    current_user: User,
    task: Task,
    attachment_type: str,
) -> None:
    """Ensure current user can upload attachment to task."""

    ensure_can_view_task(current_user, task=task)

    if task.deleted_at_utc is not None:
        raise TaskNotFoundError("Görev bulunamadı.")

    if task.status in {
        TASK_STATUS_APPROVED,
        TASK_STATUS_CANCELLED,
    }:
        raise TaskAttachmentPermissionError(
            "Onaylanmış veya iptal edilmiş göreve artık fotoğraf eklenemez."
        )

    if count_active_task_attachments(
        db,
        task_id=task.id,
        attachment_type=attachment_type,
    ) >= MAX_ATTACHMENTS_PER_TASK:
        if attachment_type == TASK_ATTACHMENT_TYPE_REFERENCE:
            raise TaskAttachmentLimitError(
                f"Bir göreve en fazla {MAX_ATTACHMENTS_PER_TASK} referans fotoğrafı eklenebilir."
            )

        raise TaskAttachmentLimitError(
            f"Bir göreve en fazla {MAX_ATTACHMENTS_PER_TASK} kanıt fotoğrafı eklenebilir."
        )


def get_task_attachment_or_error(
    db: Session,
    *,
    attachment_id: int,
) -> TaskAttachment:
    """Return task attachment by id or raise."""

    attachment = db.get(TaskAttachment, attachment_id)

    if attachment is None:
        raise TaskAttachmentNotFoundError("Görev eki bulunamadı.")

    return attachment


def ensure_attachment_belongs_to_task(
    *,
    attachment: TaskAttachment,
    task: Task,
) -> None:
    """Ensure attachment belongs to selected task."""

    if attachment.task_id != task.id or attachment.business_id != task.business_id:
        raise TaskAttachmentNotFoundError("Görev eki bulunamadı.")


def upload_task_attachment(
    db: Session,
    *,
    current_user: User,
    task: Task,
    upload_file: UploadFile,
    attachment_type: str = TASK_ATTACHMENT_TYPE_EVIDENCE,
    latitude: float | None = None,
    longitude: float | None = None,
    location_accuracy: float | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TaskAttachment:
    """Upload, optimize, store, and register task attachment."""

    normalized_attachment_type = validate_task_attachment_type_value(attachment_type)

    ensure_task_allows_attachment_upload(
        db=db,
        current_user=current_user,
        task=task,
        attachment_type=normalized_attachment_type,
    )
    validate_upload_file_metadata(upload_file)

    original_content = read_upload_file_content(upload_file)
    optimized_content, optimized_size = convert_image_to_optimized_jpeg(original_content)

    physical_path, relative_path = build_safe_storage_path(task)
    physical_path.parent.mkdir(parents=True, exist_ok=True)
    physical_path.write_bytes(optimized_content)

    try:
        if normalized_attachment_type == TASK_ATTACHMENT_TYPE_REFERENCE:
            event_type = "task_reference_photo_uploaded"
            event_note = "Göreve referans fotoğrafı yüklendi."
        else:
            event_type = "task_evidence_photo_uploaded"
            event_note = "Göreve fotoğraf kanıtı yüklendi."

        event = create_task_event(
            db=db,
            task=task,
            user_id=current_user.id,
            event_type=event_type,
            old_status=task.status,
            new_status=task.status,
            note=event_note,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.flush()

        now = get_utc_now()

        attachment = TaskAttachment(
            business_id=task.business_id,
            task_id=task.id,
            event_id=event.id,
            uploaded_by_user_id=current_user.id,
            file_path=relative_path,
            file_name=physical_path.name,
            attachment_type=normalized_attachment_type,
            file_type="image/jpeg",
            file_size=optimized_size,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            created_at_utc=now,
        )

        db.add(attachment)
        db.flush()

        return attachment
    except Exception:
        if physical_path.exists() and physical_path.is_file():
            physical_path.unlink()

        raise


def list_task_attachments(
    db: Session,
    *,
    current_user: User,
    task: Task,
    attachment_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> TaskAttachmentListResult:
    """List task attachments according to task access rules."""

    ensure_can_view_task(current_user, task=task)

    normalized_attachment_type = None

    if attachment_type is not None:
        normalized_attachment_type = validate_task_attachment_type_value(attachment_type)

    count_query = select(func.count(TaskAttachment.id)).where(TaskAttachment.task_id == task.id)
    list_query = select(TaskAttachment).where(TaskAttachment.task_id == task.id)

    if normalized_attachment_type is not None:
        count_query = count_query.where(TaskAttachment.attachment_type == normalized_attachment_type)
        list_query = list_query.where(TaskAttachment.attachment_type == normalized_attachment_type)

    total_count = int(db.execute(count_query).scalar_one())

    attachments = (
        db.execute(
            list_query
            .order_by(TaskAttachment.id.asc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return TaskAttachmentListResult(
        attachments=attachments,
        total_count=total_count,
    )


def delete_physical_attachment_file(file_path: str) -> None:
    """Delete physical attachment file if it exists under storage root."""

    path = resolve_safe_task_attachment_storage_path(file_path)

    if path.exists() and path.is_file():
        path.unlink()


def delete_task_attachment(
    db: Session,
    *,
    current_user: User,
    task: Task,
    attachment: TaskAttachment,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> int:
    """Delete task attachment record and physical file."""

    ensure_can_view_task(current_user, task=task)
    ensure_attachment_belongs_to_task(attachment=attachment, task=task)

    if task.status in {
        TASK_STATUS_APPROVED,
        TASK_STATUS_CANCELLED,
    }:
        raise TaskAttachmentPermissionError(
            "Onaylanmış veya iptal edilmiş görevden fotoğraf silinemez."
        )

    attachment_id = attachment.id
    file_path = attachment.file_path

    delete_physical_attachment_file(file_path)

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_attachment_deleted",
        old_status=task.status,
        new_status=task.status,
        note=f"Görev fotoğraf kanıtı silindi. attachment_id={attachment_id}",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.delete(attachment)
    db.flush()

    return attachment_id


def map_task_attachment_service_error(exc: Exception) -> TaskServiceError:
    """Normalize attachment service errors for route layer compatibility."""

    if isinstance(exc, TaskServiceError):
        return exc

    if isinstance(exc, TaskAttachmentNotFoundError):
        return TaskServiceError(str(exc))

    if isinstance(exc, TaskAttachmentPermissionError):
        return TaskPermissionError(str(exc))

    if isinstance(
        exc,
        (
            TaskAttachmentFileError,
            TaskAttachmentLimitError,
            TaskAttachmentServiceError,
        ),
    ):
        return TaskServiceError(str(exc))

    return TaskServiceError("Görev eki işlemi tamamlanamadı.")