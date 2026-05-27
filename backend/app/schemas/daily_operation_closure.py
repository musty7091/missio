from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


def normalize_optional_text_value(value: object) -> object:
    if value is None:
        return None

    if not isinstance(value, str):
        return value

    normalized_value = value.strip()

    if not normalized_value:
        return None

    return normalized_value


class CreateDailyOperationClosureRequest(BaseModel):
    """Request payload for closing a business operation day."""

    closure_date: date | None = None
    manager_note: str | None = Field(default=None, max_length=5000)

    @field_validator("manager_note", mode="before")
    @classmethod
    def normalize_manager_note(cls, value: object) -> object:
        return normalize_optional_text_value(value)


class DailyOperationClosureItemResponse(BaseModel):
    """Task snapshot row inside a closure report."""

    id: int
    closure_id: int
    business_id: int
    task_id: int
    task_date: date
    assigned_to_user_id: int | None
    assigned_to_user_full_name: str | None
    assigned_to_username: str | None
    task_title: str
    task_description: str | None
    task_type: str
    task_status: str
    task_priority: str
    requires_photo: bool
    requires_location: bool
    requires_manager_approval: bool
    has_photo_evidence: bool
    assigned_at_utc: datetime | None
    started_at_utc: datetime | None
    completed_at_utc: datetime | None
    approved_at_utc: datetime | None
    created_at_utc: datetime


class DailyOperationClosureResponse(BaseModel):
    """Official end-of-day closure report response."""

    id: int
    business_id: int
    closure_date: date
    closed_by_user_id: int | None
    closed_by_user_full_name: str
    closed_by_username: str
    closed_by_role: str
    closed_at_utc: datetime
    status: str
    manager_note: str | None
    closed_by_system: bool
    total_task_count: int
    completed_task_count: int
    approved_task_count: int
    open_task_count: int
    rejected_task_count: int
    approval_pending_task_count: int
    photo_required_task_count: int
    photo_evidence_task_count: int
    created_at_utc: datetime
    items: list[DailyOperationClosureItemResponse] = []


class DailyOperationClosureCreatedResponse(BaseModel):
    """Response returned after creating an end-of-day closure."""

    closure: DailyOperationClosureResponse
    message: str


class DailyOperationClosureListResponse(BaseModel):
    """Response for closure report list screen."""

    closures: list[DailyOperationClosureResponse]
    total_count: int



class AutomaticDailyClosureBusinessResultResponse(BaseModel):
    """One business result returned by the system auto-close endpoint."""

    business_id: int
    business_name: str
    closure_date: date | None
    status: str
    message: str
    closure_id: int | None = None


class AutomaticDailyClosureRunResponse(BaseModel):
    """Summary returned by the system auto-close endpoint."""

    checked_count: int
    closed_count: int
    skipped_count: int
    failed_count: int
    results: list[AutomaticDailyClosureBusinessResultResponse]
