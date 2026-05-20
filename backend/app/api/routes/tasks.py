from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.roles import UserRole
from app.db.session import get_db
from app.models.business import Business
from app.models.task import Task
from app.models.task_template import TaskTemplate
from app.models.user import User
from app.schemas.task import (
    BusinessTaskListResponse,
    CompleteTaskRequest,
    CreateExtraTaskRequest,
    CreateRoutineTaskTemplateRequest,
    DailyRoutineTasksGeneratedResponse,
    GenerateDailyRoutineTasksRequest,
    MyTodayTasksResponse,
    RejectTaskRequest,
    TaskCreatedResponse,
    TaskResponse,
    TaskStatusChangedResponse,
    TaskTemplateCreatedResponse,
    TaskTemplateResponse,
    TaskTemplateUpdatedResponse,
    TaskUpdatedResponse,
    UpdateRoutineTaskTemplateRequest,
    UpdateTaskRequest,
)
from app.services.task_service import (
    InvalidTaskAssigneeError,
    InvalidTaskStatusTransitionError,
    RoutineTaskGenerationError,
    TaskEvidenceRequiredError,
    TaskLocationRequiredError,
    TaskNotFoundError,
    TaskPermissionError,
    TaskServiceError,
    TaskTemplateNotFoundError,
    approve_task,
    cancel_task,
    create_extra_task,
    create_routine_task_template,
    generate_daily_routine_tasks,
    get_my_today_tasks,
    get_task_detail,
    get_task_or_error,
    get_task_template_or_error,
    list_business_tasks,
    list_incomplete_tasks_for_report,
    reject_task,
    soft_delete_task,
    start_task,
    update_routine_task_template,
    update_task,
)


router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_client_ip(request: Request) -> str | None:
    """Return best-effort client IP address."""

    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()[:100]

    if request.client is None:
        return None

    return request.client.host[:100]


def get_user_agent(request: Request) -> str | None:
    """Return normalized user agent from request headers."""

    user_agent = request.headers.get("user-agent")

    if not user_agent:
        return None

    return user_agent.strip()[:1000]


def map_task_service_error(exc: Exception) -> HTTPException:
    """Map task service exceptions to HTTP exceptions."""

    if isinstance(exc, (TaskNotFoundError, TaskTemplateNotFoundError)):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, TaskPermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(
        exc,
        (
            InvalidTaskAssigneeError,
            InvalidTaskStatusTransitionError,
            TaskEvidenceRequiredError,
            TaskLocationRequiredError,
            RoutineTaskGenerationError,
            TaskServiceError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Görev işlemi tamamlanamadı.",
    )


def get_business_or_404(db: Session, *, business_id: int) -> Business:
    """Return business by id or raise 404."""

    business = db.get(Business, business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı.",
        )

    return business


def get_user_or_404(db: Session, *, user_id: int) -> User:
    """Return user by id or raise 404."""

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı.",
        )

    return user


def resolve_business_for_current_user(
    db: Session,
    *,
    current_user: User,
    business_id: int | None = None,
) -> Business:
    """Resolve business scope for current user."""

    if current_user.role == UserRole.SUPER_ADMIN.value:
        if business_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super admin işlemleri için business_id gereklidir.",
            )

        return get_business_or_404(db=db, business_id=business_id)

    if current_user.business_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcının işletme kapsamı yok.",
        )

    if business_id is not None and business_id != current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işletme verisine erişim yetkiniz yok.",
        )

    return get_business_or_404(db=db, business_id=current_user.business_id)


def build_task_response(task: Task) -> TaskResponse:
    """Build safe task response."""

    return TaskResponse(
        id=task.id,
        business_id=task.business_id,
        template_id=task.template_id,
        title=task.title,
        description=task.description,
        category_id=task.category_id,
        assigned_to_user_id=task.assigned_to_user_id,
        created_by_user_id=task.created_by_user_id,
        task_type=task.task_type,
        task_date=task.task_date,
        priority=task.priority,
        status=task.status,
        due_at_utc=task.due_at_utc,
        assigned_at_utc=task.assigned_at_utc,
        started_at_utc=task.started_at_utc,
        customer_arrived_at_utc=task.customer_arrived_at_utc,
        completed_at_utc=task.completed_at_utc,
        approved_at_utc=task.approved_at_utc,
        requires_photo=task.requires_photo,
        requires_location=task.requires_location,
        requires_manager_approval=task.requires_manager_approval,
        created_at_utc=task.created_at_utc,
        updated_at_utc=task.updated_at_utc,
    )


def build_task_template_response(template: TaskTemplate) -> TaskTemplateResponse:
    """Build safe routine task template response."""

    return TaskTemplateResponse(
        id=template.id,
        business_id=template.business_id,
        assigned_to_user_id=template.assigned_to_user_id,
        created_by_user_id=template.created_by_user_id,
        title=template.title,
        description=template.description,
        category_id=template.category_id,
        recurrence_type=template.recurrence_type,
        default_priority=template.default_priority,
        default_due_time_local=template.default_due_time_local,
        default_due_offset_minutes=template.default_due_offset_minutes,
        requires_photo=template.requires_photo,
        requires_location=template.requires_location,
        requires_manager_approval=template.requires_manager_approval,
        is_active=template.is_active,
        created_at_utc=template.created_at_utc,
        updated_at_utc=template.updated_at_utc,
    )


@router.post(
    "/routine-templates",
    response_model=TaskTemplateCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_routine_task_template_endpoint(
    payload: CreateRoutineTaskTemplateRequest,
    request: Request,
    business_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskTemplateCreatedResponse:
    """Create a daily routine task template."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )
        assigned_to_user = get_user_or_404(
            db=db,
            user_id=payload.assigned_to_user_id,
        )

        template = create_routine_task_template(
            db=db,
            current_user=current_user,
            business=business,
            assigned_to_user=assigned_to_user,
            title=payload.title,
            description=payload.description,
            category_id=payload.category_id,
            recurrence_type=payload.recurrence_type,
            default_priority=payload.default_priority,
            default_due_time_local=payload.default_due_time_local,
            default_due_offset_minutes=payload.default_due_offset_minutes,
            requires_photo=payload.requires_photo,
            requires_location=payload.requires_location,
            requires_manager_approval=payload.requires_manager_approval,
        )

        db.commit()
        db.refresh(template)

        return TaskTemplateCreatedResponse(
            template=build_task_template_response(template),
            message="Rutin görev şablonu oluşturuldu.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.get(
    "/routine-templates",
    response_model=list[TaskTemplateResponse],
)
def list_routine_task_templates_endpoint(
    business_id: int | None = Query(default=None, gt=0),
    assigned_to_user_id: int | None = Query(default=None, gt=0),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskTemplateResponse]:
    """List routine task templates."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        if current_user.role == UserRole.STAFF.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Personel rutin görev şablonlarını yönetemez.",
            )

        query = select(TaskTemplate).where(TaskTemplate.business_id == business.id)

        if assigned_to_user_id is not None:
            query = query.where(TaskTemplate.assigned_to_user_id == assigned_to_user_id)

        if is_active is not None:
            query = query.where(TaskTemplate.is_active.is_(is_active))

        templates = (
            db.execute(
                query.order_by(
                    TaskTemplate.assigned_to_user_id.asc(),
                    TaskTemplate.id.asc(),
                )
            )
            .scalars()
            .all()
        )

        return [build_task_template_response(template) for template in templates]
    except HTTPException:
        raise
    except Exception as exc:
        raise map_task_service_error(exc) from exc


@router.patch(
    "/routine-templates/{template_id}",
    response_model=TaskTemplateUpdatedResponse,
)
def update_routine_task_template_endpoint(
    template_id: int,
    payload: UpdateRoutineTaskTemplateRequest,
    request: Request,
    business_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskTemplateUpdatedResponse:
    """Update a daily routine task template."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )
        template = get_task_template_or_error(db=db, template_id=template_id)

        assigned_to_user = None

        if "assigned_to_user_id" in payload.model_fields_set:
            if payload.assigned_to_user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="assigned_to_user_id boş olamaz.",
                )

            assigned_to_user = get_user_or_404(
                db=db,
                user_id=payload.assigned_to_user_id,
            )

        updated_template = update_routine_task_template(
            db=db,
            current_user=current_user,
            business=business,
            template=template,
            update_fields=payload.model_fields_set,
            assigned_to_user=assigned_to_user,
            title=payload.title,
            description=payload.description,
            category_id=payload.category_id,
            recurrence_type=payload.recurrence_type,
            default_priority=payload.default_priority,
            default_due_time_local=payload.default_due_time_local,
            default_due_offset_minutes=payload.default_due_offset_minutes,
            requires_photo=payload.requires_photo,
            requires_location=payload.requires_location,
            requires_manager_approval=payload.requires_manager_approval,
            is_active=payload.is_active,
        )

        db.commit()
        db.refresh(updated_template)

        return TaskTemplateUpdatedResponse(
            template=build_task_template_response(updated_template),
            message="Rutin görev şablonu güncellendi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.post(
    "/extra",
    response_model=TaskCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_extra_task_endpoint(
    payload: CreateExtraTaskRequest,
    request: Request,
    business_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskCreatedResponse:
    """Create an extra one-off task."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )
        assigned_to_user = get_user_or_404(
            db=db,
            user_id=payload.assigned_to_user_id,
        )

        task = create_extra_task(
            db=db,
            current_user=current_user,
            business=business,
            assigned_to_user=assigned_to_user,
            title=payload.title,
            description=payload.description,
            category_id=payload.category_id,
            priority=payload.priority,
            due_at_utc=payload.due_at_utc,
            requires_photo=payload.requires_photo,
            requires_location=payload.requires_location,
            requires_manager_approval=payload.requires_manager_approval,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(task)

        return TaskCreatedResponse(
            task=build_task_response(task),
            message="Ekstra görev oluşturuldu.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.post(
    "/generate-daily-routines",
    response_model=DailyRoutineTasksGeneratedResponse,
)
def generate_daily_routine_tasks_endpoint(
    payload: GenerateDailyRoutineTasksRequest,
    request: Request,
    business_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyRoutineTasksGeneratedResponse:
    """Generate daily tasks from active routine templates."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        result = generate_daily_routine_tasks(
            db=db,
            current_user=current_user,
            business=business,
            task_date=payload.task_date,
            assigned_to_user_id=payload.assigned_to_user_id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()

        for task in result.tasks:
            db.refresh(task)

        return DailyRoutineTasksGeneratedResponse(
            task_date=result.task_date,
            created_count=result.created_count,
            skipped_count=result.skipped_count,
            tasks=[build_task_response(task) for task in result.tasks],
            message="Günlük rutin görevler üretildi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.get(
    "/my-today",
    response_model=MyTodayTasksResponse,
)
def get_my_today_tasks_endpoint(
    request: Request,
    business_id: int | None = Query(default=None, gt=0),
    task_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MyTodayTasksResponse:
    """Return current user's routine and extra tasks for selected day.

    If daily routine tasks do not exist yet, they are generated automatically.
    """

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        result = get_my_today_tasks(
            db=db,
            current_user=current_user,
            business=business,
            task_date=task_date,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()

        for task in result.routine_tasks:
            db.refresh(task)

        for task in result.extra_tasks:
            db.refresh(task)

        return MyTodayTasksResponse(
            task_date=result.task_date,
            routine_tasks=[build_task_response(task) for task in result.routine_tasks],
            extra_tasks=[build_task_response(task) for task in result.extra_tasks],
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.get(
    "",
    response_model=BusinessTaskListResponse,
)
def list_business_tasks_endpoint(
    business_id: int | None = Query(default=None, gt=0),
    task_date: date | None = Query(default=None),
    task_type: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    assigned_to_user_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessTaskListResponse:
    """List business tasks."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        result = list_business_tasks(
            db=db,
            current_user=current_user,
            business=business,
            task_date=task_date,
            task_type=task_type,
            status=status_value,
            assigned_to_user_id=assigned_to_user_id,
            limit=limit,
            offset=offset,
        )

        return BusinessTaskListResponse(
            tasks=[build_task_response(task) for task in result.tasks],
            total_count=result.total_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise map_task_service_error(exc) from exc

@router.get(
    "/reports/incomplete",
    response_model=BusinessTaskListResponse,
)
def list_incomplete_tasks_for_report_endpoint(
    task_date: date,
    business_id: int | None = Query(default=None, gt=0),
    assigned_to_user_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessTaskListResponse:
    """List incomplete tasks for end-of-day report."""

    try:
        business = resolve_business_for_current_user(
            db=db,
            current_user=current_user,
            business_id=business_id,
        )

        result = list_incomplete_tasks_for_report(
            db=db,
            current_user=current_user,
            business=business,
            task_date=task_date,
            assigned_to_user_id=assigned_to_user_id,
            limit=limit,
            offset=offset,
        )

        return BusinessTaskListResponse(
            tasks=[build_task_response(task) for task in result.tasks],
            total_count=result.total_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise map_task_service_error(exc) from exc

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task_detail_endpoint(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """Return task detail."""

    try:
        task = get_task_detail(
            db=db,
            current_user=current_user,
            task_id=task_id,
        )

        return build_task_response(task)
    except Exception as exc:
        raise map_task_service_error(exc) from exc


@router.patch(
    "/{task_id}",
    response_model=TaskUpdatedResponse,
)
def update_task_endpoint(
    task_id: int,
    payload: UpdateTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskUpdatedResponse:
    """Update task definition."""

    try:
        task = get_task_or_error(db=db, task_id=task_id)

        assigned_to_user = None

        if "assigned_to_user_id" in payload.model_fields_set:
            if payload.assigned_to_user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="assigned_to_user_id boş olamaz.",
                )

            assigned_to_user = get_user_or_404(
                db=db,
                user_id=payload.assigned_to_user_id,
            )

        updated_task = update_task(
            db=db,
            current_user=current_user,
            task=task,
            update_fields=payload.model_fields_set,
            assigned_to_user=assigned_to_user,
            title=payload.title,
            description=payload.description,
            category_id=payload.category_id,
            priority=payload.priority,
            due_at_utc=payload.due_at_utc,
            requires_photo=payload.requires_photo,
            requires_location=payload.requires_location,
            requires_manager_approval=payload.requires_manager_approval,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(updated_task)

        return TaskUpdatedResponse(
            task=build_task_response(updated_task),
            message="Görev güncellendi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.post(
    "/{task_id}/start",
    response_model=TaskStatusChangedResponse,
)
def start_task_endpoint(
    task_id: int,
    payload: CompleteTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusChangedResponse:
    """Start assigned task."""

    try:
        task = get_task_or_error(db=db, task_id=task_id)

        started_task = start_task(
            db=db,
            current_user=current_user,
            task=task,
            note=payload.note,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_accuracy=payload.location_accuracy,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(started_task)

        return TaskStatusChangedResponse(
            task=build_task_response(started_task),
            message="Görev başlatıldı.",
        )
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.post(
    "/{task_id}/complete",
    response_model=TaskStatusChangedResponse,
)
def complete_task_endpoint(
    task_id: int,
    payload: CompleteTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusChangedResponse:
    """Complete assigned task."""

    try:
        task = get_task_or_error(db=db, task_id=task_id)

        completed_task = complete_task(
            db=db,
            current_user=current_user,
            task=task,
            note=payload.note,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_accuracy=payload.location_accuracy,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(completed_task)

        return TaskStatusChangedResponse(
            task=build_task_response(completed_task),
            message="Görev tamamlandı.",
        )
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.post(
    "/{task_id}/approve",
    response_model=TaskStatusChangedResponse,
)
def approve_task_endpoint(
    task_id: int,
    payload: CompleteTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusChangedResponse:
    """Approve completed task."""

    try:
        task = get_task_or_error(db=db, task_id=task_id)

        approved_task = approve_task(
            db=db,
            current_user=current_user,
            task=task,
            note=payload.note,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(approved_task)

        return TaskStatusChangedResponse(
            task=build_task_response(approved_task),
            message="Görev onaylandı.",
        )
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.post(
    "/{task_id}/reject",
    response_model=TaskStatusChangedResponse,
)
def reject_task_endpoint(
    task_id: int,
    payload: RejectTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusChangedResponse:
    """Reject completed task."""

    try:
        task = get_task_or_error(db=db, task_id=task_id)

        rejected_task = reject_task(
            db=db,
            current_user=current_user,
            task=task,
            note=payload.note,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(rejected_task)

        return TaskStatusChangedResponse(
            task=build_task_response(rejected_task),
            message="Görev reddedildi.",
        )
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.post(
    "/{task_id}/cancel",
    response_model=TaskStatusChangedResponse,
)
def cancel_task_endpoint(
    task_id: int,
    payload: CompleteTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusChangedResponse:
    """Cancel task."""

    try:
        task = get_task_or_error(db=db, task_id=task_id)

        cancelled_task = cancel_task(
            db=db,
            current_user=current_user,
            task=task,
            note=payload.note,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(cancelled_task)

        return TaskStatusChangedResponse(
            task=build_task_response(cancelled_task),
            message="Görev iptal edildi.",
        )
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc


@router.delete(
    "/{task_id}",
    response_model=TaskStatusChangedResponse,
)
def delete_task_endpoint(
    task_id: int,
    payload: CompleteTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusChangedResponse:
    """Soft delete task."""

    try:
        task = get_task_or_error(db=db, task_id=task_id)

        deleted_task = soft_delete_task(
            db=db,
            current_user=current_user,
            task=task,
            note=payload.note,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(deleted_task)

        return TaskStatusChangedResponse(
            task=build_task_response(deleted_task),
            message="Görev silindi.",
        )
    except Exception as exc:
        db.rollback()
        raise map_task_service_error(exc) from exc