from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, Field, field_validator, model_validator


TASK_TYPE_ROUTINE = "routine"
TASK_TYPE_EXTRA = "extra"

ALLOWED_TASK_TYPES = {
    TASK_TYPE_ROUTINE,
    TASK_TYPE_EXTRA,
}

TASK_STATUS_ASSIGNED = "assigned"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_APPROVED = "approved"
TASK_STATUS_REJECTED = "rejected"
TASK_STATUS_CANCELLED = "cancelled"

ALLOWED_TASK_STATUSES = {
    TASK_STATUS_ASSIGNED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_APPROVED,
    TASK_STATUS_REJECTED,
    TASK_STATUS_CANCELLED,
}

TASK_PRIORITY_LOW = "low"
TASK_PRIORITY_NORMAL = "normal"
TASK_PRIORITY_HIGH = "high"
TASK_PRIORITY_URGENT = "urgent"

ALLOWED_TASK_PRIORITIES = {
    TASK_PRIORITY_LOW,
    TASK_PRIORITY_NORMAL,
    TASK_PRIORITY_HIGH,
    TASK_PRIORITY_URGENT,
}

RECURRENCE_TYPE_DAILY = "daily"

ALLOWED_RECURRENCE_TYPES = {
    RECURRENCE_TYPE_DAILY,
}


def normalize_optional_text_value(value: object) -> object:
    """Trim optional text value and convert empty strings to None."""

    if value is None:
        return None

    if not isinstance(value, str):
        return value

    normalized_value = value.strip()

    if not normalized_value:
        return None

    return normalized_value


def normalize_required_text_value(value: object) -> object:
    """Trim required text value."""

    if isinstance(value, str):
        return value.strip()

    return value


def validate_task_priority_value(value: str) -> str:
    """Validate task priority value."""

    normalized_value = value.strip().lower()

    if normalized_value not in ALLOWED_TASK_PRIORITIES:
        raise ValueError("Görev önceliği geçersiz.")

    return normalized_value


def validate_task_status_value(value: str) -> str:
    """Validate task status value."""

    normalized_value = value.strip().lower()

    if normalized_value not in ALLOWED_TASK_STATUSES:
        raise ValueError("Görev durumu geçersiz.")

    return normalized_value


def validate_recurrence_type_value(value: str) -> str:
    """Validate recurrence type value."""

    normalized_value = value.strip().lower()

    if normalized_value not in ALLOWED_RECURRENCE_TYPES:
        raise ValueError("Rutin görev tekrar tipi geçersiz.")

    return normalized_value


class CreateRoutineTaskTemplateRequest(BaseModel):
    """Request payload for creating a daily routine task template."""

    assigned_to_user_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None, gt=0)
    recurrence_type: str = Field(default=RECURRENCE_TYPE_DAILY, min_length=3, max_length=30)
    default_priority: str = Field(default=TASK_PRIORITY_NORMAL, min_length=3, max_length=30)
    default_due_time_local: time | None = None
    default_due_offset_minutes: int | None = Field(default=None, ge=0, le=1440)
    requires_photo: bool = False
    requires_location: bool = False
    requires_manager_approval: bool = False

    @field_validator("title", "recurrence_type", "default_priority", mode="before")
    @classmethod
    def normalize_required_text(cls, value: object) -> object:
        """Trim required text fields."""

        return normalize_required_text_value(value)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        """Trim optional text fields and convert empty strings to None."""

        return normalize_optional_text_value(value)

    @field_validator("recurrence_type")
    @classmethod
    def validate_recurrence_type(cls, value: str) -> str:
        """Validate recurrence type."""

        return validate_recurrence_type_value(value)

    @field_validator("default_priority")
    @classmethod
    def validate_default_priority(cls, value: str) -> str:
        """Validate default task priority."""

        return validate_task_priority_value(value)

    @model_validator(mode="after")
    def validate_due_rule(self) -> CreateRoutineTaskTemplateRequest:
        """Prevent conflicting due time rules."""

        if (
            self.default_due_time_local is not None
            and self.default_due_offset_minutes is not None
        ):
            raise ValueError(
                "Rutin görev için aynı anda hem sabit saat hem süre ofseti gönderilemez."
            )

        return self


class UpdateRoutineTaskTemplateRequest(BaseModel):
    """Request payload for updating a daily routine task template."""

    assigned_to_user_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None, gt=0)
    recurrence_type: str | None = Field(default=None, min_length=3, max_length=30)
    default_priority: str | None = Field(default=None, min_length=3, max_length=30)
    default_due_time_local: time | None = None
    default_due_offset_minutes: int | None = Field(default=None, ge=0, le=1440)
    requires_photo: bool | None = None
    requires_location: bool | None = None
    requires_manager_approval: bool | None = None
    is_active: bool | None = None

    @field_validator("title", "recurrence_type", "default_priority", mode="before")
    @classmethod
    def normalize_optional_required_like_text(cls, value: object) -> object:
        """Trim optional text fields that must not become empty when provided."""

        if value is None:
            return None

        return normalize_required_text_value(value)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        """Trim optional text fields and convert empty strings to None."""

        return normalize_optional_text_value(value)

    @field_validator("recurrence_type")
    @classmethod
    def validate_recurrence_type(cls, value: str | None) -> str | None:
        """Validate recurrence type."""

        if value is None:
            return None

        return validate_recurrence_type_value(value)

    @field_validator("default_priority")
    @classmethod
    def validate_default_priority(cls, value: str | None) -> str | None:
        """Validate default task priority."""

        if value is None:
            return None

        return validate_task_priority_value(value)

    @model_validator(mode="after")
    def validate_update_payload(self) -> UpdateRoutineTaskTemplateRequest:
        """Require at least one update field and prevent conflicting due rules."""

        if not self.model_fields_set:
            raise ValueError("Güncellenecek en az bir alan gönderilmelidir.")

        if (
            "default_due_time_local" in self.model_fields_set
            and "default_due_offset_minutes" in self.model_fields_set
            and self.default_due_time_local is not None
            and self.default_due_offset_minutes is not None
        ):
            raise ValueError(
                "Rutin görev için aynı anda hem sabit saat hem süre ofseti gönderilemez."
            )

        return self


class CreateExtraTaskRequest(BaseModel):
    """Request payload for creating an extra one-off task."""

    assigned_to_user_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None, gt=0)
    priority: str = Field(default=TASK_PRIORITY_NORMAL, min_length=3, max_length=30)
    due_at_utc: datetime | None = None
    requires_photo: bool = False
    requires_location: bool = False
    requires_manager_approval: bool = False

    @field_validator("title", "priority", mode="before")
    @classmethod
    def normalize_required_text(cls, value: object) -> object:
        """Trim required text fields."""

        return normalize_required_text_value(value)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        """Trim optional text fields and convert empty strings to None."""

        return normalize_optional_text_value(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        """Validate task priority."""

        return validate_task_priority_value(value)


class UpdateTaskRequest(BaseModel):
    """Request payload for updating a task."""

    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None, gt=0)
    assigned_to_user_id: int | None = Field(default=None, gt=0)
    priority: str | None = Field(default=None, min_length=3, max_length=30)
    due_at_utc: datetime | None = None
    requires_photo: bool | None = None
    requires_location: bool | None = None
    requires_manager_approval: bool | None = None

    @field_validator("title", "priority", mode="before")
    @classmethod
    def normalize_optional_required_like_text(cls, value: object) -> object:
        """Trim optional text fields that must not become empty when provided."""

        if value is None:
            return None

        return normalize_required_text_value(value)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        """Trim optional text fields and convert empty strings to None."""

        return normalize_optional_text_value(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        """Validate task priority."""

        if value is None:
            return None

        return validate_task_priority_value(value)

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> UpdateTaskRequest:
        """Require at least one explicitly provided update field."""

        if not self.model_fields_set:
            raise ValueError("Güncellenecek en az bir alan gönderilmelidir.")

        return self


class ChangeTaskStatusRequest(BaseModel):
    """Request payload for changing task status."""

    status: str = Field(min_length=3, max_length=50)
    note: str | None = Field(default=None, max_length=5000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy: float | None = Field(default=None, ge=0)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> object:
        """Trim and lowercase status field."""

        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: object) -> object:
        """Trim optional note and convert empty strings to None."""

        return normalize_optional_text_value(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Validate task status."""

        return validate_task_status_value(value)


class CompleteTaskRequest(BaseModel):
    """Request payload for completing, starting, approving, cancelling, or deleting a task."""

    note: str | None = Field(default=None, max_length=5000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy: float | None = Field(default=None, ge=0)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: object) -> object:
        """Trim optional note and convert empty strings to None."""

        return normalize_optional_text_value(value)


class RejectTaskRequest(BaseModel):
    """Request payload for rejecting a completed task."""

    note: str = Field(min_length=2, max_length=5000)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: object) -> object:
        """Trim reject note."""

        return normalize_required_text_value(value)


class GenerateDailyRoutineTasksRequest(BaseModel):
    """Request payload for generating daily routine tasks."""

    task_date: date | None = None
    assigned_to_user_id: int | None = Field(default=None, gt=0)


class TaskResponse(BaseModel):
    """Safe task response."""

    id: int
    business_id: int
    template_id: int | None
    title: str
    description: str | None
    category_id: int | None
    assigned_to_user_id: int | None
    assigned_to_user_full_name: str | None = None
    assigned_to_username: str | None = None
    created_by_user_id: int | None
    task_type: str
    task_date: date
    priority: str
    status: str
    due_at_utc: datetime | None
    assigned_at_utc: datetime | None
    started_at_utc: datetime | None
    customer_arrived_at_utc: datetime | None
    completed_at_utc: datetime | None
    approved_at_utc: datetime | None
    requires_photo: bool
    requires_location: bool
    requires_manager_approval: bool
    created_at_utc: datetime
    updated_at_utc: datetime


class TaskEventResponse(BaseModel):
    """Safe task event response."""

    id: int
    business_id: int
    task_id: int
    user_id: int | None
    event_type: str
    old_status: str | None
    new_status: str | None
    note: str | None
    latitude: float | None
    longitude: float | None
    location_accuracy: float | None
    ip_address: str | None
    user_agent: str | None
    created_at_utc: datetime


class TaskEventListResponse(BaseModel):
    """Response for task event history."""

    events: list[TaskEventResponse]
    total_count: int


class TaskAttachmentResponse(BaseModel):
    """Safe task attachment response."""

    id: int
    business_id: int
    task_id: int
    event_id: int | None
    uploaded_by_user_id: int | None
    file_name: str
    file_type: str | None
    file_size: int | None
    latitude: float | None
    longitude: float | None
    location_accuracy: float | None
    created_at_utc: datetime


class TaskAttachmentCreatedResponse(BaseModel):
    """Response returned after uploading task attachment."""

    attachment: TaskAttachmentResponse
    message: str


class TaskAttachmentListResponse(BaseModel):
    """Response for task attachments."""

    attachments: list[TaskAttachmentResponse]
    total_count: int


class TaskAttachmentDeletedResponse(BaseModel):
    """Response returned after deleting task attachment."""

    attachment_id: int
    message: str


class TaskTemplateResponse(BaseModel):
    """Safe routine task template response."""

    id: int
    business_id: int
    assigned_to_user_id: int
    created_by_user_id: int | None
    title: str
    description: str | None
    category_id: int | None
    recurrence_type: str
    default_priority: str
    default_due_time_local: time | None
    default_due_offset_minutes: int | None
    requires_photo: bool
    requires_location: bool
    requires_manager_approval: bool
    is_active: bool
    created_at_utc: datetime
    updated_at_utc: datetime


class TaskCreatedResponse(BaseModel):
    """Response returned after creating a task."""

    task: TaskResponse
    message: str


class TaskUpdatedResponse(BaseModel):
    """Response returned after updating a task."""

    task: TaskResponse
    message: str


class TaskStatusChangedResponse(BaseModel):
    """Response returned after changing task status."""

    task: TaskResponse
    message: str


class TaskTemplateCreatedResponse(BaseModel):
    """Response returned after creating a routine task template."""

    template: TaskTemplateResponse
    message: str


class TaskTemplateUpdatedResponse(BaseModel):
    """Response returned after updating a routine task template."""

    template: TaskTemplateResponse
    message: str


class DailyRoutineTasksGeneratedResponse(BaseModel):
    """Response returned after generating daily routine tasks."""

    task_date: date
    created_count: int
    skipped_count: int
    tasks: list[TaskResponse]
    message: str


class MyTodayTasksResponse(BaseModel):
    """Response for staff or manager daily task screen."""

    task_date: date
    routine_tasks: list[TaskResponse]
    extra_tasks: list[TaskResponse]


class BusinessTaskListResponse(BaseModel):
    """Response for business task list screen."""

    tasks: list[TaskResponse]
    total_count: int
