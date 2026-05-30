from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.business import Business
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.models.task_event import TaskEvent
from app.models.task_template import TaskTemplate
from app.models.user import User
from app.models.web_push_subscription import WebPushSubscription
from app.schemas.task import (
    RECURRENCE_TYPE_DAILY,
    TASK_PRIORITY_NORMAL,
    TASK_STATUS_APPROVED,
    TASK_STATUS_ASSIGNED,
    TASK_STATUS_CANCELLED,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_REJECTED,
    TASK_ATTACHMENT_TYPE_EVIDENCE,
    TASK_TYPE_EXTRA,
    TASK_TYPE_ROUTINE,
)
from app.services.access_control_service import (
    ensure_business_scope,
    ensure_staff_task_access,
)
from app.services.web_push_service import (
    WebPushServiceError,
    send_web_push_to_subscription,
)


class TaskServiceError(ValueError):
    """Base error for task service failures."""


class TaskPermissionError(TaskServiceError):
    """Raised when user has no permission for task operation."""


class TaskNotFoundError(TaskServiceError):
    """Raised when task is not found."""


class TaskTemplateNotFoundError(TaskServiceError):
    """Raised when task template is not found."""


class InvalidTaskAssigneeError(TaskServiceError):
    """Raised when assigned user is not valid for task assignment."""


class InvalidTaskStatusTransitionError(TaskServiceError):
    """Raised when task status transition is not valid."""


class TaskEvidenceRequiredError(TaskServiceError):
    """Raised when task requires evidence before completion."""


class TaskLocationRequiredError(TaskServiceError):
    """Raised when task requires location before completion."""


class RoutineTaskGenerationError(TaskServiceError):
    """Raised when daily routine task generation fails."""


@dataclass(frozen=True)
class DailyRoutineTaskGenerationResult:
    """Result returned after generating daily routine tasks."""

    task_date: date
    created_count: int
    skipped_count: int
    tasks: list[Task]


@dataclass(frozen=True)
class TodayTasksResult:
    """Routine and extra task list for daily screen."""

    task_date: date
    routine_tasks: list[Task]
    extra_tasks: list[Task]


@dataclass(frozen=True)
class BusinessTaskListResult:
    """Business task list result."""

    tasks: list[Task]
    total_count: int


@dataclass(frozen=True)
class TaskEventListResult:
    """Task event history result."""

    events: list[TaskEvent]
    total_count: int


@dataclass(frozen=True)
class ScheduledTaskNotificationCandidate:
    """Scheduled task notification candidate."""

    task: Task
    assigned_to_user: User


TASK_ASSIGNABLE_ROLES = {
    UserRole.MANAGER.value,
    UserRole.STAFF.value,
}

TASK_MANAGER_ROLES = {
    UserRole.SUPER_ADMIN.value,
    UserRole.BOSS.value,
    UserRole.MANAGER.value,
}

BOSS_LEVEL_ROLES = {
    UserRole.BOSS.value,
}

WEB_PUSH_APPROVER_ROLES = {
    UserRole.BOSS.value,
    UserRole.MANAGER.value,
}

SCHEDULED_TASK_NOTIFICATION_WAITING_EVENT_TYPE = "extra_task_scheduled_notification_waiting"
SCHEDULED_TASK_NOTIFICATION_SENT_EVENT_TYPE = "extra_task_scheduled_notification_sent"

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def get_business_timezone(business: Business) -> ZoneInfo:
    """Return business timezone, fallback to Europe/Istanbul."""

    timezone_name = business.timezone or "Europe/Istanbul"

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Europe/Istanbul")


def get_business_today(business: Business) -> date:
    """Return current date in business timezone."""

    business_timezone = get_business_timezone(business)

    return get_utc_now().astimezone(business_timezone).date()


def normalize_datetime_to_utc(value: datetime | None) -> datetime | None:
    """Normalize datetime to timezone-aware UTC."""

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def should_defer_extra_task_assignment_notification(
    *,
    due_at_utc: datetime | None,
    now_utc: datetime | None = None,
) -> bool:
    """Return whether an extra task assignment notification must be delayed."""

    normalized_due_at_utc = normalize_datetime_to_utc(due_at_utc)

    if normalized_due_at_utc is None:
        return False

    reference_now = now_utc or get_utc_now()

    return normalized_due_at_utc > reference_now


def calculate_due_at_utc(
    *,
    business: Business,
    task_date: date,
    due_time_local: time | None = None,
    due_offset_minutes: int | None = None,
) -> datetime | None:
    """Calculate task due datetime in UTC."""

    business_timezone = get_business_timezone(business)

    if due_time_local is not None:
        local_due_datetime = datetime.combine(task_date, due_time_local).replace(
            tzinfo=business_timezone
        )

        return local_due_datetime.astimezone(timezone.utc)

    if due_offset_minutes is not None:
        local_start_of_day = datetime.combine(task_date, time(hour=0, minute=0)).replace(
            tzinfo=business_timezone
        )
        local_due_datetime = local_start_of_day + timedelta(minutes=due_offset_minutes)

        return local_due_datetime.astimezone(timezone.utc)

    return None


def get_task_or_error(db: Session, *, task_id: int) -> Task:
    """Return active task by id or raise."""

    task = db.get(Task, task_id)

    if task is None or task.deleted_at_utc is not None:
        raise TaskNotFoundError("Görev bulunamadı.")

    return task


def get_task_template_or_error(db: Session, *, template_id: int) -> TaskTemplate:
    """Return task template by id or raise."""

    template = db.get(TaskTemplate, template_id)

    if template is None:
        raise TaskTemplateNotFoundError("Rutin görev şablonu bulunamadı.")

    return template


def ensure_task_manager_access(
    current_user: User,
    *,
    business_id: int,
) -> None:
    """Ensure user can manage tasks in business."""

    ensure_business_scope(current_user, business_id)

    if current_user.role in TASK_MANAGER_ROLES:
        return

    raise TaskPermissionError("Bu işlem için görev yönetim yetkiniz yok.")


def ensure_user_can_be_assigned_to_task(
    target_user: User,
    *,
    business_id: int,
) -> None:
    """Ensure target user can receive tasks."""

    if target_user.business_id != business_id:
        raise InvalidTaskAssigneeError("Görev atanacak kullanıcı bu işletmeye ait değil.")

    if not target_user.is_active:
        raise InvalidTaskAssigneeError("Pasif kullanıcıya görev atanamaz.")

    if target_user.role not in TASK_ASSIGNABLE_ROLES:
        raise InvalidTaskAssigneeError(
            "Görev sadece manager veya staff kullanıcısına atanabilir."
        )


def ensure_can_assign_task_to_user(
    current_user: User,
    *,
    target_user: User,
    business_id: int,
) -> None:
    """Ensure current user can assign task to target user."""

    ensure_business_scope(current_user, business_id)
    ensure_user_can_be_assigned_to_task(target_user, business_id=business_id)

    if current_user.role == UserRole.SUPER_ADMIN.value:
        return

    if current_user.role in BOSS_LEVEL_ROLES:
        return

    if current_user.role == UserRole.MANAGER.value:
        if target_user.role == UserRole.STAFF.value:
            return

        raise TaskPermissionError("Manager sadece personel kullanıcısına görev atayabilir.")

    raise TaskPermissionError("Bu kullanıcı görev atayamaz.")


def ensure_can_view_task(current_user: User, *, task: Task) -> None:
    """Ensure current user can view task."""

    ensure_staff_task_access(
        current_user,
        task_business_id=task.business_id,
        assigned_to_user_id=task.assigned_to_user_id,
    )


def ensure_can_update_task(current_user: User, *, task: Task) -> None:
    """Ensure current user can update task definition."""

    ensure_task_manager_access(
        current_user,
        business_id=task.business_id,
    )


def ensure_can_perform_task(current_user: User, *, task: Task) -> None:
    """Ensure current user can start or complete assigned task."""

    ensure_can_view_task(current_user, task=task)

    if task.assigned_to_user_id != current_user.id:
        raise TaskPermissionError(
            "Bu görevi sadece atanan kullanıcı başlatabilir veya tamamlayabilir."
        )


def ensure_task_belongs_to_business(task: Task, *, business_id: int) -> None:
    """Ensure task belongs to business."""

    if task.business_id != business_id:
        raise TaskPermissionError("Bu görev ilgili işletmeye ait değil.")


def ensure_template_belongs_to_business(
    template: TaskTemplate,
    *,
    business_id: int,
) -> None:
    """Ensure task template belongs to business."""

    if template.business_id != business_id:
        raise TaskPermissionError("Bu rutin görev şablonu ilgili işletmeye ait değil.")


def count_task_attachments(
    db: Session,
    *,
    task_id: int,
    attachment_type: str | None = None,
) -> int:
    """Return attachment count for task, optionally filtered by attachment type."""

    query = select(func.count(TaskAttachment.id)).where(TaskAttachment.task_id == task_id)

    if attachment_type is not None:
        query = query.where(TaskAttachment.attachment_type == attachment_type)

    return int(db.execute(query).scalar_one())


def create_task_event(
    db: Session,
    *,
    task: Task,
    user_id: int | None,
    event_type: str,
    old_status: str | None = None,
    new_status: str | None = None,
    note: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_accuracy: float | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TaskEvent:
    """Create task event record."""

    event = TaskEvent(
        business_id=task.business_id,
        task_id=task.id,
        user_id=user_id,
        event_type=event_type,
        old_status=old_status,
        new_status=new_status,
        note=note,
        latitude=latitude,
        longitude=longitude,
        location_accuracy=location_accuracy,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at_utc=get_utc_now(),
    )

    db.add(event)

    return event


def has_task_event_type(
    db: Session,
    *,
    task_id: int,
    event_type: str,
) -> bool:
    """Return whether a task event type already exists for task."""

    event_id = db.execute(
        select(TaskEvent.id)
        .where(
            TaskEvent.task_id == task_id,
            TaskEvent.event_type == event_type,
        )
        .limit(1)
    ).scalar_one_or_none()

    return event_id is not None


def create_scheduled_task_notification_waiting_event(
    db: Session,
    *,
    task: Task,
    user_id: int | None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TaskEvent:
    """Record that an extra task assignment notification is waiting for its due time."""

    if has_task_event_type(
        db,
        task_id=task.id,
        event_type=SCHEDULED_TASK_NOTIFICATION_WAITING_EVENT_TYPE,
    ):
        return db.execute(
            select(TaskEvent)
            .where(
                TaskEvent.task_id == task.id,
                TaskEvent.event_type == SCHEDULED_TASK_NOTIFICATION_WAITING_EVENT_TYPE,
            )
            .order_by(TaskEvent.id.asc())
            .limit(1)
        ).scalar_one()

    return create_task_event(
        db=db,
        task=task,
        user_id=user_id,
        event_type=SCHEDULED_TASK_NOTIFICATION_WAITING_EVENT_TYPE,
        old_status=None,
        new_status=task.status,
        note="Planlı görev bildirimi seçilen tarih ve saate kadar bekletildi.",
        ip_address=ip_address,
        user_agent=user_agent,
    )


def create_scheduled_task_notification_sent_event(
    db: Session,
    *,
    task: Task,
    attempted_count: int,
    sent_count: int,
    failed_count: int,
) -> TaskEvent | None:
    """Record that a scheduled assignment notification was already processed."""

    if has_task_event_type(
        db,
        task_id=task.id,
        event_type=SCHEDULED_TASK_NOTIFICATION_SENT_EVENT_TYPE,
    ):
        return None

    return create_task_event(
        db=db,
        task=task,
        user_id=None,
        event_type=SCHEDULED_TASK_NOTIFICATION_SENT_EVENT_TYPE,
        old_status=task.status,
        new_status=task.status,
        note=(
            "Planlı görev bildirimi işlendi. "
            f"Deneme: {attempted_count}, başarılı: {sent_count}, başarısız: {failed_count}."
        ),
    )


def build_task_web_push_url(task: Task) -> str:
    """Return frontend deep-link URL for a task notification."""

    return f"/?missioOpen=task&missioTaskId={task.id}"


def get_task_push_title(task: Task) -> str:
    """Return safe task title for notification body."""

    title = (task.title or "").strip()

    if not title:
        return f"Görev #{task.id}"

    if len(title) > 80:
        return f"{title[:77]}..."

    return title


def get_active_web_push_subscriptions_for_user_ids(
    db: Session,
    *,
    user_ids: list[int],
    business_id: int,
) -> list[WebPushSubscription]:
    """Return active Web Push subscriptions for target users."""

    unique_user_ids = sorted({user_id for user_id in user_ids if user_id > 0})

    if not unique_user_ids:
        return []

    return (
        db.query(WebPushSubscription)
        .filter(
            WebPushSubscription.business_id == business_id,
            WebPushSubscription.user_id.in_(unique_user_ids),
            WebPushSubscription.is_active.is_(True),
        )
        .order_by(WebPushSubscription.id.desc())
        .all()
    )


def send_task_web_push_to_user_ids(
    db: Session,
    *,
    business_id: int,
    user_ids: list[int],
    task: Task,
    title: str,
    body: str,
    event_type: str,
) -> None:
    """Best-effort task Web Push delivery. It must never block task workflow."""

    subscriptions = get_active_web_push_subscriptions_for_user_ids(
        db=db,
        user_ids=user_ids,
        business_id=business_id,
    )

    if not subscriptions:
        return

    for subscription in subscriptions:
        try:
            send_web_push_to_subscription(
                db=db,
                subscription=subscription,
                title=title,
                body=body,
                url=build_task_web_push_url(task),
                tag=f"missio-task-{task.id}-{event_type}",
                data={
                    "type": event_type,
                    "task_id": str(task.id),
                    "business_id": str(task.business_id),
                    "url": build_task_web_push_url(task),
                },
            )
        except WebPushServiceError as exc:
            logger.warning(
                "MISSIO_WEB_PUSH_SEND_FAILED subscription_id=%s user_id=%s task_id=%s event_type=%s error=%s",
                subscription.id,
                subscription.user_id,
                task.id,
                event_type,
                exc,
            )
        except Exception as exc:
            logger.warning(
                "MISSIO_WEB_PUSH_UNEXPECTED_ERROR subscription_id=%s user_id=%s task_id=%s event_type=%s error=%s",
                subscription.id,
                subscription.user_id,
                task.id,
                event_type,
                exc,
            )


def get_task_approval_notification_user_ids(
    db: Session,
    *,
    task: Task,
    exclude_user_id: int | None = None,
) -> list[int]:
    """
    Return users who must be notified when a task is completed.

    Business rule:
    - Business boss users must be informed.
    - The user who created/assigned the task must be informed.
    - The user who completed the task must not receive a self-notification.
    - Unrelated managers must not receive noise notifications.
    """

    recipient_user_ids: set[int] = set()

    boss_user_rows = (
        db.query(User.id)
        .filter(
            User.business_id == task.business_id,
            User.is_active.is_(True),
            User.role == UserRole.BOSS.value,
        )
        .all()
    )

    for row in boss_user_rows:
        recipient_user_ids.add(int(row[0]))

    if task.created_by_user_id is not None:
        creator = db.get(User, task.created_by_user_id)

        if (
            creator is not None
            and creator.is_active
            and creator.business_id == task.business_id
        ):
            recipient_user_ids.add(creator.id)

    if exclude_user_id is not None:
        recipient_user_ids.discard(exclude_user_id)

    return sorted(recipient_user_ids)


def notify_task_assigned(
    db: Session,
    *,
    task: Task,
    assigned_to_user: User,
) -> None:
    """Notify assigned user that a new task is available."""

    send_task_web_push_to_user_ids(
        db=db,
        business_id=task.business_id,
        user_ids=[assigned_to_user.id],
        task=task,
        title="Yeni görev atandı",
        body=f"Sana yeni bir görev atandı: {get_task_push_title(task)}",
        event_type="task_assigned",
    )


def notify_task_completed(
    db: Session,
    *,
    task: Task,
    completed_by_user: User,
) -> None:
    """Notify boss/manager users when a task is completed."""

    recipient_user_ids = get_task_approval_notification_user_ids(
        db=db,
        task=task,
        exclude_user_id=completed_by_user.id,
    )

    if task.requires_manager_approval:
        title = "Görev onay bekliyor"
        body = f"{completed_by_user.full_name} görevi tamamladı, onay bekliyor: {get_task_push_title(task)}"
        event_type = "task_waiting_approval"
    else:
        title = "Görev tamamlandı"
        body = f"{completed_by_user.full_name} görevi tamamladı: {get_task_push_title(task)}"
        event_type = "task_completed"

    send_task_web_push_to_user_ids(
        db=db,
        business_id=task.business_id,
        user_ids=recipient_user_ids,
        task=task,
        title=title,
        body=body,
        event_type=event_type,
    )


def notify_task_approved(
    db: Session,
    *,
    task: Task,
) -> None:
    """Notify assigned user that the task was approved."""

    if task.assigned_to_user_id is None:
        return

    send_task_web_push_to_user_ids(
        db=db,
        business_id=task.business_id,
        user_ids=[task.assigned_to_user_id],
        task=task,
        title="Görev onaylandı",
        body=f"Görevin onaylandı: {get_task_push_title(task)}",
        event_type="task_approved",
    )


def notify_task_rejected(
    db: Session,
    *,
    task: Task,
) -> None:
    """Notify assigned user that the task was rejected."""

    if task.assigned_to_user_id is None:
        return

    send_task_web_push_to_user_ids(
        db=db,
        business_id=task.business_id,
        user_ids=[task.assigned_to_user_id],
        task=task,
        title="Görev reddedildi",
        body=f"Görevin düzeltme için geri gönderildi: {get_task_push_title(task)}",
        event_type="task_rejected",
    )


def create_routine_task_template(
    db: Session,
    *,
    current_user: User,
    business: Business,
    assigned_to_user: User,
    title: str,
    description: str | None = None,
    category_id: int | None = None,
    recurrence_type: str = RECURRENCE_TYPE_DAILY,
    default_priority: str = TASK_PRIORITY_NORMAL,
    default_due_time_local: time | None = None,
    default_due_offset_minutes: int | None = None,
    requires_photo: bool = False,
    requires_location: bool = False,
    requires_manager_approval: bool = False,
) -> TaskTemplate:
    """Create daily routine task template."""

    ensure_can_assign_task_to_user(
        current_user,
        target_user=assigned_to_user,
        business_id=business.id,
    )

    if recurrence_type != RECURRENCE_TYPE_DAILY:
        raise TaskServiceError("Şimdilik sadece daily rutin görev destekleniyor.")

    now = get_utc_now()

    template = TaskTemplate(
        business_id=business.id,
        assigned_to_user_id=assigned_to_user.id,
        created_by_user_id=current_user.id,
        title=title.strip(),
        description=description.strip() if description else None,
        category_id=category_id,
        recurrence_type=recurrence_type,
        default_priority=default_priority,
        default_due_time_local=default_due_time_local,
        default_due_offset_minutes=default_due_offset_minutes,
        requires_photo=requires_photo,
        requires_location=requires_location,
        requires_manager_approval=requires_manager_approval,
        is_active=True,
        created_at_utc=now,
        updated_at_utc=now,
    )

    db.add(template)
    db.flush()

    return template


def update_routine_task_template(
    db: Session,
    *,
    current_user: User,
    business: Business,
    template: TaskTemplate,
    update_fields: set[str],
    assigned_to_user: User | None = None,
    title: str | None = None,
    description: str | None = None,
    category_id: int | None = None,
    recurrence_type: str | None = None,
    default_priority: str | None = None,
    default_due_time_local: time | None = None,
    default_due_offset_minutes: int | None = None,
    requires_photo: bool | None = None,
    requires_location: bool | None = None,
    requires_manager_approval: bool | None = None,
    is_active: bool | None = None,
) -> TaskTemplate:
    """Update daily routine task template."""

    ensure_template_belongs_to_business(template, business_id=business.id)
    ensure_task_manager_access(current_user, business_id=business.id)

    if "assigned_to_user_id" in update_fields:
        if assigned_to_user is None:
            raise InvalidTaskAssigneeError("Atanacak kullanıcı bulunamadı.")

        ensure_can_assign_task_to_user(
            current_user,
            target_user=assigned_to_user,
            business_id=business.id,
        )
        template.assigned_to_user_id = assigned_to_user.id

    if "title" in update_fields:
        if title is None:
            raise TaskServiceError("Rutin görev başlığı boş olamaz.")

        template.title = title.strip()

    if "description" in update_fields:
        template.description = description.strip() if description else None

    if "category_id" in update_fields:
        template.category_id = category_id

    if "recurrence_type" in update_fields:
        if recurrence_type != RECURRENCE_TYPE_DAILY:
            raise TaskServiceError("Şimdilik sadece daily rutin görev destekleniyor.")

        template.recurrence_type = recurrence_type

    if "default_priority" in update_fields:
        if default_priority is None:
            raise TaskServiceError("Rutin görev önceliği boş olamaz.")

        template.default_priority = default_priority

    if "default_due_time_local" in update_fields:
        template.default_due_time_local = default_due_time_local

    if "default_due_offset_minutes" in update_fields:
        template.default_due_offset_minutes = default_due_offset_minutes

    if "requires_photo" in update_fields:
        if requires_photo is None:
            raise TaskServiceError("requires_photo boş olamaz.")

        template.requires_photo = requires_photo

    if "requires_location" in update_fields:
        if requires_location is None:
            raise TaskServiceError("requires_location boş olamaz.")

        template.requires_location = requires_location

    if "requires_manager_approval" in update_fields:
        if requires_manager_approval is None:
            raise TaskServiceError("requires_manager_approval boş olamaz.")

        template.requires_manager_approval = requires_manager_approval

    if "is_active" in update_fields:
        if is_active is None:
            raise TaskServiceError("is_active boş olamaz.")

        template.is_active = is_active

    template.updated_at_utc = get_utc_now()

    db.add(template)
    db.flush()

    return template


def create_extra_task(
    db: Session,
    *,
    current_user: User,
    business: Business,
    assigned_to_user: User,
    title: str,
    description: str | None = None,
    category_id: int | None = None,
    priority: str = TASK_PRIORITY_NORMAL,
    due_at_utc: datetime | None = None,
    requires_photo: bool = False,
    requires_location: bool = False,
    requires_manager_approval: bool = False,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Create one-off extra task."""

    ensure_can_assign_task_to_user(
        current_user,
        target_user=assigned_to_user,
        business_id=business.id,
    )

    now = get_utc_now()
    normalized_due_at_utc = normalize_datetime_to_utc(due_at_utc)
    business_timezone = get_business_timezone(business)

    if normalized_due_at_utc is not None:
        task_date = normalized_due_at_utc.astimezone(business_timezone).date()
    else:
        task_date = get_business_today(business)

    task = Task(
        business_id=business.id,
        template_id=None,
        title=title.strip(),
        description=description.strip() if description else None,
        category_id=category_id,
        assigned_to_user_id=assigned_to_user.id,
        created_by_user_id=current_user.id,
        task_type=TASK_TYPE_EXTRA,
        task_date=task_date,
        priority=priority,
        status=TASK_STATUS_ASSIGNED,
        due_at_utc=normalized_due_at_utc,
        assigned_at_utc=now,
        started_at_utc=None,
        customer_arrived_at_utc=None,
        completed_at_utc=None,
        approved_at_utc=None,
        requires_photo=requires_photo,
        requires_location=requires_location,
        requires_manager_approval=requires_manager_approval,
        created_at_utc=now,
        updated_at_utc=now,
        deleted_at_utc=None,
    )

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="extra_task_created",
        old_status=None,
        new_status=task.status,
        note="Ekstra görev oluşturuldu.",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if should_defer_extra_task_assignment_notification(due_at_utc=task.due_at_utc, now_utc=now):
        create_scheduled_task_notification_waiting_event(
            db=db,
            task=task,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # Ekstra görev bildirimi route katmanında, ana işlem commit edildikten sonra
    # tek kez gönderilir. Böylece çift bildirim ve bildirim hatasının görev
    # oluşturmayı bozması engellenir.

    return task


def generate_daily_routine_tasks(
    db: Session,
    *,
    current_user: User,
    business: Business,
    task_date: date | None = None,
    assigned_to_user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> DailyRoutineTaskGenerationResult:
    """Generate daily tasks from active routine templates."""

    ensure_task_manager_access(current_user, business_id=business.id)

    selected_task_date = task_date or get_business_today(business)

    template_query = select(TaskTemplate).where(
        TaskTemplate.business_id == business.id,
        TaskTemplate.is_active.is_(True),
        TaskTemplate.recurrence_type == RECURRENCE_TYPE_DAILY,
    )

    if assigned_to_user_id is not None:
        template_query = template_query.where(
            TaskTemplate.assigned_to_user_id == assigned_to_user_id
        )

    templates = db.execute(
        template_query.order_by(TaskTemplate.assigned_to_user_id.asc(), TaskTemplate.id.asc())
    ).scalars().all()

    created_tasks: list[Task] = []
    skipped_count = 0
    now = get_utc_now()

    for template in templates:
        assigned_user = db.get(User, template.assigned_to_user_id)

        if assigned_user is None:
            skipped_count += 1
            continue

        if not assigned_user.is_active:
            skipped_count += 1
            continue

        if assigned_user.business_id != business.id:
            skipped_count += 1
            continue

        if assigned_user.role not in TASK_ASSIGNABLE_ROLES:
            skipped_count += 1
            continue

        existing_task = db.execute(
            select(Task).where(
                Task.business_id == business.id,
                Task.template_id == template.id,
                Task.assigned_to_user_id == template.assigned_to_user_id,
                Task.task_date == selected_task_date,
                Task.deleted_at_utc.is_(None),
            )
        ).scalar_one_or_none()

        if existing_task is not None:
            skipped_count += 1
            continue

        due_at_utc = calculate_due_at_utc(
            business=business,
            task_date=selected_task_date,
            due_time_local=template.default_due_time_local,
            due_offset_minutes=template.default_due_offset_minutes,
        )

        task = Task(
            business_id=business.id,
            template_id=template.id,
            title=template.title,
            description=template.description,
            category_id=template.category_id,
            assigned_to_user_id=template.assigned_to_user_id,
            created_by_user_id=current_user.id,
            task_type=TASK_TYPE_ROUTINE,
            task_date=selected_task_date,
            priority=template.default_priority,
            status=TASK_STATUS_ASSIGNED,
            due_at_utc=due_at_utc,
            assigned_at_utc=now,
            started_at_utc=None,
            customer_arrived_at_utc=None,
            completed_at_utc=None,
            approved_at_utc=None,
            requires_photo=template.requires_photo,
            requires_location=template.requires_location,
            requires_manager_approval=template.requires_manager_approval,
            created_at_utc=now,
            updated_at_utc=now,
            deleted_at_utc=None,
        )

        db.add(task)
        db.flush()

        create_task_event(
            db=db,
            task=task,
            user_id=current_user.id,
            event_type="routine_task_generated",
            old_status=None,
            new_status=task.status,
            note="Günlük rutin görev üretildi.",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        notify_task_assigned(
            db=db,
            task=task,
            assigned_to_user=assigned_user,
        )

        created_tasks.append(task)

    return DailyRoutineTaskGenerationResult(
        task_date=selected_task_date,
        created_count=len(created_tasks),
        skipped_count=skipped_count,
        tasks=created_tasks,
    )


def ensure_daily_routine_tasks_for_assigned_user(
    db: Session,
    *,
    current_user: User,
    business: Business,
    task_date: date | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> DailyRoutineTaskGenerationResult:
    """Ensure current user's daily routine tasks exist."""

    ensure_business_scope(current_user, business.id)

    if current_user.business_id != business.id:
        raise TaskPermissionError("Kullanıcı bu işletmeye ait değil.")

    if current_user.role not in TASK_ASSIGNABLE_ROLES:
        raise TaskPermissionError("Bu kullanıcıya günlük rutin görev üretilemez.")

    selected_task_date = task_date or get_business_today(business)

    templates = (
        db.execute(
            select(TaskTemplate)
            .where(
                TaskTemplate.business_id == business.id,
                TaskTemplate.assigned_to_user_id == current_user.id,
                TaskTemplate.is_active.is_(True),
                TaskTemplate.recurrence_type == RECURRENCE_TYPE_DAILY,
            )
            .order_by(TaskTemplate.id.asc())
        )
        .scalars()
        .all()
    )

    created_tasks: list[Task] = []
    skipped_count = 0
    now = get_utc_now()

    for template in templates:
        existing_task = db.execute(
            select(Task).where(
                Task.business_id == business.id,
                Task.template_id == template.id,
                Task.assigned_to_user_id == current_user.id,
                Task.task_date == selected_task_date,
                Task.deleted_at_utc.is_(None),
            )
        ).scalar_one_or_none()

        if existing_task is not None:
            skipped_count += 1
            continue

        due_at_utc = calculate_due_at_utc(
            business=business,
            task_date=selected_task_date,
            due_time_local=template.default_due_time_local,
            due_offset_minutes=template.default_due_offset_minutes,
        )

        task = Task(
            business_id=business.id,
            template_id=template.id,
            title=template.title,
            description=template.description,
            category_id=template.category_id,
            assigned_to_user_id=current_user.id,
            created_by_user_id=template.created_by_user_id,
            task_type=TASK_TYPE_ROUTINE,
            task_date=selected_task_date,
            priority=template.default_priority,
            status=TASK_STATUS_ASSIGNED,
            due_at_utc=due_at_utc,
            assigned_at_utc=now,
            started_at_utc=None,
            customer_arrived_at_utc=None,
            completed_at_utc=None,
            approved_at_utc=None,
            requires_photo=template.requires_photo,
            requires_location=template.requires_location,
            requires_manager_approval=template.requires_manager_approval,
            created_at_utc=now,
            updated_at_utc=now,
            deleted_at_utc=None,
        )

        db.add(task)
        db.flush()

        create_task_event(
            db=db,
            task=task,
            user_id=current_user.id,
            event_type="routine_task_auto_generated",
            old_status=None,
            new_status=task.status,
            note="Günlük rutin görev otomatik oluşturuldu.",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        created_tasks.append(task)

    return DailyRoutineTaskGenerationResult(
        task_date=selected_task_date,
        created_count=len(created_tasks),
        skipped_count=skipped_count,
        tasks=created_tasks,
    )


def get_my_today_tasks(
    db: Session,
    *,
    current_user: User,
    business: Business,
    task_date: date | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TodayTasksResult:
    """Return current user's routine and extra tasks for selected day."""

    ensure_business_scope(current_user, business.id)

    if current_user.business_id != business.id:
        raise TaskPermissionError("Kullanıcı bu işletmeye ait değil.")

    selected_task_date = task_date or get_business_today(business)

    ensure_daily_routine_tasks_for_assigned_user(
        db=db,
        current_user=current_user,
        business=business,
        task_date=selected_task_date,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    tasks = (
        db.execute(
            select(Task)
            .where(
                Task.business_id == business.id,
                Task.assigned_to_user_id == current_user.id,
                Task.task_date == selected_task_date,
                Task.deleted_at_utc.is_(None),
            )
            .order_by(Task.task_type.desc(), Task.id.asc())
        )
        .scalars()
        .all()
    )

    routine_tasks = [task for task in tasks if task.task_type == TASK_TYPE_ROUTINE]
    extra_tasks = [task for task in tasks if task.task_type == TASK_TYPE_EXTRA]

    return TodayTasksResult(
        task_date=selected_task_date,
        routine_tasks=routine_tasks,
        extra_tasks=extra_tasks,
    )


def list_business_tasks(
    db: Session,
    *,
    current_user: User,
    business: Business,
    task_date: date | None = None,
    task_type: str | None = None,
    status: str | None = None,
    assigned_to_user_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> BusinessTaskListResult:
    """List business tasks according to user access."""

    ensure_business_scope(current_user, business.id)

    query = select(Task).where(
        Task.business_id == business.id,
        Task.deleted_at_utc.is_(None),
    )

    count_query = select(func.count(Task.id)).where(
        Task.business_id == business.id,
        Task.deleted_at_utc.is_(None),
    )

    if current_user.role == UserRole.STAFF.value:
        query = query.where(Task.assigned_to_user_id == current_user.id)
        count_query = count_query.where(Task.assigned_to_user_id == current_user.id)

    if task_date is not None:
        query = query.where(Task.task_date == task_date)
        count_query = count_query.where(Task.task_date == task_date)

    if task_type is not None:
        query = query.where(Task.task_type == task_type)
        count_query = count_query.where(Task.task_type == task_type)

    if status is not None:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)

    if assigned_to_user_id is not None:
        if current_user.role == UserRole.STAFF.value and assigned_to_user_id != current_user.id:
            raise TaskPermissionError("Personel sadece kendi görevlerini listeleyebilir.")

        query = query.where(Task.assigned_to_user_id == assigned_to_user_id)
        count_query = count_query.where(Task.assigned_to_user_id == assigned_to_user_id)

    total_count = int(db.execute(count_query).scalar_one())

    tasks = (
        db.execute(
            query.order_by(Task.task_date.desc(), Task.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return BusinessTaskListResult(
        tasks=tasks,
        total_count=total_count,
    )


def list_incomplete_tasks_for_report(
    db: Session,
    *,
    current_user: User,
    business: Business,
    task_date: date,
    assigned_to_user_id: int | None = None,
    limit: int = 500,
    offset: int = 0,
) -> BusinessTaskListResult:
    """List incomplete tasks for end-of-day reporting."""

    ensure_task_manager_access(current_user, business_id=business.id)

    incomplete_statuses = {
        TASK_STATUS_ASSIGNED,
        TASK_STATUS_IN_PROGRESS,
        TASK_STATUS_REJECTED,
    }

    query = select(Task).where(
        Task.business_id == business.id,
        Task.task_date == task_date,
        Task.status.in_(incomplete_statuses),
        Task.deleted_at_utc.is_(None),
    )

    count_query = select(func.count(Task.id)).where(
        Task.business_id == business.id,
        Task.task_date == task_date,
        Task.status.in_(incomplete_statuses),
        Task.deleted_at_utc.is_(None),
    )

    if assigned_to_user_id is not None:
        query = query.where(Task.assigned_to_user_id == assigned_to_user_id)
        count_query = count_query.where(Task.assigned_to_user_id == assigned_to_user_id)

    total_count = int(db.execute(count_query).scalar_one())

    tasks = (
        db.execute(
            query.order_by(
                Task.assigned_to_user_id.asc(),
                Task.task_type.desc(),
                Task.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return BusinessTaskListResult(
        tasks=tasks,
        total_count=total_count,
    )


def get_task_detail(
    db: Session,
    *,
    current_user: User,
    task_id: int,
) -> Task:
    """Return task detail according to access rules."""

    task = get_task_or_error(db, task_id=task_id)
    ensure_can_view_task(current_user, task=task)

    return task


def list_task_events(
    db: Session,
    *,
    current_user: User,
    task: Task,
    limit: int = 100,
    offset: int = 0,
) -> TaskEventListResult:
    """List task event history according to task access rules."""

    ensure_can_view_task(current_user, task=task)

    count_query = select(func.count(TaskEvent.id)).where(TaskEvent.task_id == task.id)

    total_count = int(db.execute(count_query).scalar_one())

    events = (
        db.execute(
            select(TaskEvent)
            .where(TaskEvent.task_id == task.id)
            .order_by(TaskEvent.id.asc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return TaskEventListResult(
        events=events,
        total_count=total_count,
    )


def update_task(
    db: Session,
    *,
    current_user: User,
    task: Task,
    update_fields: set[str],
    assigned_to_user: User | None = None,
    title: str | None = None,
    description: str | None = None,
    category_id: int | None = None,
    priority: str | None = None,
    due_at_utc: datetime | None = None,
    requires_photo: bool | None = None,
    requires_location: bool | None = None,
    requires_manager_approval: bool | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Update task definition."""

    ensure_can_update_task(current_user, task=task)

    old_status = task.status

    if "assigned_to_user_id" in update_fields:
        if assigned_to_user is None:
            raise InvalidTaskAssigneeError("Atanacak kullanıcı bulunamadı.")

        ensure_can_assign_task_to_user(
            current_user,
            target_user=assigned_to_user,
            business_id=task.business_id,
        )
        task.assigned_to_user_id = assigned_to_user.id
        task.assigned_at_utc = get_utc_now()

    if "title" in update_fields:
        if title is None:
            raise TaskServiceError("Görev başlığı boş olamaz.")

        task.title = title.strip()

    if "description" in update_fields:
        task.description = description.strip() if description else None

    if "category_id" in update_fields:
        task.category_id = category_id

    if "priority" in update_fields:
        if priority is None:
            raise TaskServiceError("Görev önceliği boş olamaz.")

        task.priority = priority

    if "due_at_utc" in update_fields:
        task.due_at_utc = normalize_datetime_to_utc(due_at_utc)

    if "requires_photo" in update_fields:
        if requires_photo is None:
            raise TaskServiceError("requires_photo boş olamaz.")

        task.requires_photo = requires_photo

    if "requires_location" in update_fields:
        if requires_location is None:
            raise TaskServiceError("requires_location boş olamaz.")

        task.requires_location = requires_location

    if "requires_manager_approval" in update_fields:
        if requires_manager_approval is None:
            raise TaskServiceError("requires_manager_approval boş olamaz.")

        task.requires_manager_approval = requires_manager_approval

    task.updated_at_utc = get_utc_now()

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_updated",
        old_status=old_status,
        new_status=task.status,
        note="Görev güncellendi.",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return task


def list_due_scheduled_extra_task_notification_candidates(
    db: Session,
    *,
    now_utc: datetime | None = None,
    limit: int = 100,
) -> list[ScheduledTaskNotificationCandidate]:
    """Return due scheduled extra tasks whose assignment notification was not processed."""

    reference_now = now_utc or get_utc_now()

    waiting_event_exists = (
        select(TaskEvent.id)
        .where(
            TaskEvent.task_id == Task.id,
            TaskEvent.event_type == SCHEDULED_TASK_NOTIFICATION_WAITING_EVENT_TYPE,
        )
        .exists()
    )
    sent_event_exists = (
        select(TaskEvent.id)
        .where(
            TaskEvent.task_id == Task.id,
            TaskEvent.event_type == SCHEDULED_TASK_NOTIFICATION_SENT_EVENT_TYPE,
        )
        .exists()
    )

    rows = (
        db.execute(
            select(Task, User)
            .join(User, Task.assigned_to_user_id == User.id)
            .where(
                Task.deleted_at_utc.is_(None),
                Task.task_type == TASK_TYPE_EXTRA,
                Task.status == TASK_STATUS_ASSIGNED,
                Task.assigned_to_user_id.is_not(None),
                Task.due_at_utc.is_not(None),
                Task.due_at_utc <= reference_now,
                waiting_event_exists,
                ~sent_event_exists,
                User.is_active.is_(True),
                User.business_id == Task.business_id,
            )
            .order_by(Task.due_at_utc.asc(), Task.id.asc())
            .limit(limit)
        )
        .all()
    )

    return [
        ScheduledTaskNotificationCandidate(task=task, assigned_to_user=assigned_to_user)
        for task, assigned_to_user in rows
    ]


def start_task(
    db: Session,
    *,
    current_user: User,
    task: Task,
    note: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_accuracy: float | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Start assigned task."""

    ensure_can_perform_task(current_user, task=task)

    if task.status != TASK_STATUS_ASSIGNED:
        raise InvalidTaskStatusTransitionError("Sadece atanmış görev başlatılabilir.")

    if task.requires_location and (latitude is None or longitude is None):
        raise TaskLocationRequiredError("Bu görevi başlatmak için konum bilgisi gereklidir.")

    old_status = task.status

    task.status = TASK_STATUS_IN_PROGRESS
    task.started_at_utc = get_utc_now()
    task.updated_at_utc = task.started_at_utc

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_started",
        old_status=old_status,
        new_status=task.status,
        note=note,
        latitude=latitude,
        longitude=longitude,
        location_accuracy=location_accuracy,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return task


def complete_task(
    db: Session,
    *,
    current_user: User,
    task: Task,
    note: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_accuracy: float | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Complete assigned task."""

    ensure_can_perform_task(current_user, task=task)

    if task.status not in {
        TASK_STATUS_ASSIGNED,
        TASK_STATUS_IN_PROGRESS,
        TASK_STATUS_REJECTED,
    }:
        raise InvalidTaskStatusTransitionError(
            "Sadece atanmış, başlamış veya reddedilmiş görev tamamlanabilir."
        )

    if task.requires_location and (latitude is None or longitude is None):
        raise TaskLocationRequiredError("Bu görevi tamamlamak için konum bilgisi gereklidir.")

    if task.requires_photo and count_task_attachments(
        db,
        task_id=task.id,
        attachment_type=TASK_ATTACHMENT_TYPE_EVIDENCE,
    ) < 1:
        raise TaskEvidenceRequiredError(
            "Bu görevi tamamlamak için en az bir kanıt fotoğrafı gereklidir."
        )

    old_status = task.status

    task.status = TASK_STATUS_COMPLETED
    task.completed_at_utc = get_utc_now()
    task.updated_at_utc = task.completed_at_utc

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_completed",
        old_status=old_status,
        new_status=task.status,
        note=note,
        latitude=latitude,
        longitude=longitude,
        location_accuracy=location_accuracy,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    notify_task_completed(
        db=db,
        task=task,
        completed_by_user=current_user,
    )

    return task


def approve_task(
    db: Session,
    *,
    current_user: User,
    task: Task,
    note: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Approve completed task."""

    ensure_task_manager_access(current_user, business_id=task.business_id)

    if task.status != TASK_STATUS_COMPLETED:
        raise InvalidTaskStatusTransitionError("Sadece tamamlanmış görev onaylanabilir.")

    old_status = task.status

    task.status = TASK_STATUS_APPROVED
    task.approved_at_utc = get_utc_now()
    task.updated_at_utc = task.approved_at_utc

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_approved",
        old_status=old_status,
        new_status=task.status,
        note=note,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    notify_task_approved(
        db=db,
        task=task,
    )

    return task


def reject_task(
    db: Session,
    *,
    current_user: User,
    task: Task,
    note: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Reject completed task."""

    ensure_task_manager_access(current_user, business_id=task.business_id)

    if task.status != TASK_STATUS_COMPLETED:
        raise InvalidTaskStatusTransitionError("Sadece tamamlanmış görev reddedilebilir.")

    old_status = task.status

    task.status = TASK_STATUS_REJECTED
    task.updated_at_utc = get_utc_now()

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_rejected",
        old_status=old_status,
        new_status=task.status,
        note=note,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    notify_task_rejected(
        db=db,
        task=task,
    )

    return task


def cancel_task(
    db: Session,
    *,
    current_user: User,
    task: Task,
    note: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Cancel task."""

    ensure_task_manager_access(current_user, business_id=task.business_id)

    if task.status in {
        TASK_STATUS_APPROVED,
        TASK_STATUS_CANCELLED,
    }:
        raise InvalidTaskStatusTransitionError("Bu görev artık iptal edilemez.")

    old_status = task.status

    task.status = TASK_STATUS_CANCELLED
    task.updated_at_utc = get_utc_now()

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_cancelled",
        old_status=old_status,
        new_status=task.status,
        note=note,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return task


def soft_delete_task(
    db: Session,
    *,
    current_user: User,
    task: Task,
    note: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Task:
    """Soft delete task."""

    ensure_task_manager_access(current_user, business_id=task.business_id)

    task.deleted_at_utc = get_utc_now()
    task.updated_at_utc = task.deleted_at_utc

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task=task,
        user_id=current_user.id,
        event_type="task_deleted",
        old_status=task.status,
        new_status=task.status,
        note=note or "Görev silindi.",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return task