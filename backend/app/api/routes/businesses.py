from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.roles import UserRole
from app.db.session import get_db
from app.models.business import Business
from app.models.business_subscription import BusinessSubscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.business import (
    BusinessOwnerUserResponse,
    BusinessResponse,
    BusinessSubscriptionPlanChangedResponse,
    BusinessSubscriptionOverviewResponse,
    BusinessSubscriptionResponse,
    BusinessWithOwnerCreatedResponse,
    ChangeBusinessSubscriptionPlanRequest,
    ChangeBusinessPlanRequest,
    CreateBusinessWithOwnerRequest,
    ExtendBusinessSubscriptionRequest,
    UpdateBusinessSubscriptionStatusRequest,
    SubscriptionPlanResponse,
)
from app.services.access_control_service import AccessControlError, require_roles
from app.services.auth_service import (
    AuthServiceError,
    DuplicateUsernameError,
    WeakPasswordError,
)
from app.services.business_service import (
    BusinessServiceError,
    DuplicateBusinessSlugError,
    InvalidBusinessOwnerRoleError,
    InvalidBusinessSlugError,
    create_business_with_owner,
)
from app.services.subscription_service import (
    BusinessNotFoundForSubscriptionError,
    BusinessSubscriptionCannotBeExtendedError,
    BusinessSubscriptionStatusUpdateError,
    SubscriptionPlanNotFoundError,
    SubscriptionPlanUserLimitTooLowError,
    SubscriptionServiceError,
    change_business_subscription_plan,
    change_business_plan,
    extend_business_subscription,
    update_business_subscription_status,
    count_active_business_users,
    get_current_business_subscription,
    list_active_subscription_plans,
)


router = APIRouter(prefix="/businesses", tags=["businesses"])


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


def build_business_response(
    business: Business,
    *,
    subscription: BusinessSubscription | None = None,
    plan: SubscriptionPlan | None = None,
) -> BusinessResponse:
    """Build safe business response."""

    subscription_remaining_days = (
        calculate_remaining_days(subscription.ends_at_utc)
        if subscription is not None
        else None
    )

    return BusinessResponse(
        id=business.id,
        name=business.name,
        slug=business.slug,
        logo_path=business.logo_path,
        owner_name=business.owner_name,
        phone=business.phone,
        email=business.email,
        address=business.address,
        timezone=business.timezone,
        default_theme=business.default_theme,
        is_active=business.is_active,
        created_at=business.created_at,
        updated_at=business.updated_at,
        subscription_status=subscription.status if subscription is not None else None,
        subscription_billing_period=(
            subscription.billing_period if subscription is not None else None
        ),
        subscription_plan_code=plan.code if plan is not None else None,
        subscription_plan_name=plan.name if plan is not None else None,
        subscription_ends_at_utc=(
            subscription.ends_at_utc if subscription is not None else None
        ),
        subscription_max_users=(
            subscription.max_users_snapshot if subscription is not None else None
        ),
        subscription_remaining_days=subscription_remaining_days,
    )


def build_business_owner_user_response(user: User) -> BusinessOwnerUserResponse:
    """Build safe first owner user response."""

    if user.business_id is None:
        raise RuntimeError("İşletme sahibi kullanıcısında business_id boş olamaz.")

    return BusinessOwnerUserResponse(
        id=user.id,
        business_id=user.business_id,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


def build_business_subscription_response(
    subscription: BusinessSubscription,
) -> BusinessSubscriptionResponse:
    """Build safe business subscription response."""

    return BusinessSubscriptionResponse(
        id=subscription.id,
        business_id=subscription.business_id,
        plan_id=subscription.plan_id,
        status=subscription.status,
        billing_period=subscription.billing_period,
        starts_at_utc=subscription.starts_at_utc,
        ends_at_utc=subscription.ends_at_utc,
        is_current=subscription.is_current,
        max_users_snapshot=subscription.max_users_snapshot,
        max_managers_snapshot=subscription.max_managers_snapshot,
        max_daily_tasks_snapshot=subscription.max_daily_tasks_snapshot,
        report_retention_days_snapshot=subscription.report_retention_days_snapshot,
    )


def build_subscription_plan_response(plan: SubscriptionPlan) -> SubscriptionPlanResponse:
    """Build safe subscription plan response."""

    return SubscriptionPlanResponse(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        description=plan.description,
        max_users=plan.max_users,
        max_managers=plan.max_managers,
        max_daily_tasks=plan.max_daily_tasks,
        report_retention_days=plan.report_retention_days,
        price_monthly=str(plan.price_monthly) if plan.price_monthly is not None else None,
        price_yearly=str(plan.price_yearly) if plan.price_yearly is not None else None,
        currency=plan.currency,
        display_order=plan.display_order,
        is_active=plan.is_active,
    )


def get_utc_now_for_route() -> datetime:
    """Return current UTC datetime for route-level calculations."""

    return datetime.now(timezone.utc)


def as_utc_aware_for_route(value: datetime | None) -> datetime | None:
    """Normalize datetime value for route-level comparisons."""

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def calculate_remaining_days(value: datetime | None) -> int | None:
    """Calculate remaining whole days until given datetime."""

    normalized_value = as_utc_aware_for_route(value)

    if normalized_value is None:
        return None

    now = get_utc_now_for_route()
    seconds = (normalized_value - now).total_seconds()

    if seconds < 0:
        return 0

    return int((seconds + 86_399) // 86_400)


@router.get("", response_model=list[BusinessResponse])
def list_businesses_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BusinessResponse]:
    """List all businesses for super admin panel with subscription summary."""

    try:
        require_roles(current_user, [UserRole.SUPER_ADMIN])

        businesses = (
            db.execute(
                select(Business)
                .order_by(Business.created_at.desc(), Business.id.desc())
            )
            .scalars()
            .all()
        )

        response_items: list[BusinessResponse] = []

        for business in businesses:
            subscription = get_current_business_subscription(
                db=db,
                business_id=business.id,
            )
            plan = None

            if subscription is not None:
                plan = (
                    db.query(SubscriptionPlan)
                    .filter(SubscriptionPlan.id == subscription.plan_id)
                    .one_or_none()
                )

            response_items.append(
                build_business_response(
                    business,
                    subscription=subscription,
                    plan=plan,
                )
            )

        return response_items
    except AccessControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc


@router.get("/subscription-plans", response_model=list[SubscriptionPlanResponse])
def list_subscription_plans_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubscriptionPlanResponse]:
    """List active subscription plans for super admin panel."""

    try:
        require_roles(current_user, [UserRole.SUPER_ADMIN])

        plans = list_active_subscription_plans(db=db)

        return [build_subscription_plan_response(plan) for plan in plans]
    except AccessControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc


@router.get(
    "/{business_id}/subscription/current",
    response_model=BusinessSubscriptionResponse | None,
)
def get_current_business_subscription_endpoint(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessSubscriptionResponse | None:
    """Return current business subscription for super admin panel."""

    try:
        require_roles(current_user, [UserRole.SUPER_ADMIN])

        business = db.query(Business).filter(Business.id == business_id).one_or_none()

        if business is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="İşletme bulunamadı.",
            )

        subscription = get_current_business_subscription(
            db=db,
            business_id=business.id,
        )

        if subscription is None:
            return None

        return build_business_subscription_response(subscription)
    except HTTPException:
        raise
    except AccessControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc



@router.get(
    "/{business_id}/subscription/overview",
    response_model=BusinessSubscriptionOverviewResponse,
)
def get_business_subscription_overview_endpoint(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessSubscriptionOverviewResponse:
    """Return detailed subscription overview for super admin panel."""

    try:
        require_roles(current_user, [UserRole.SUPER_ADMIN])

        business = db.query(Business).filter(Business.id == business_id).one_or_none()

        if business is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="İşletme bulunamadı.",
            )

        current_subscription = get_current_business_subscription(
            db=db,
            business_id=business.id,
        )

        current_plan = None

        if current_subscription is not None:
            current_plan = (
                db.query(SubscriptionPlan)
                .filter(SubscriptionPlan.id == current_subscription.plan_id)
                .one_or_none()
            )

        active_user_count = count_active_business_users(
            db=db,
            business_id=business.id,
        )

        ends_at_utc = (
            current_subscription.ends_at_utc
            if current_subscription is not None
            else None
        )
        normalized_ends_at_utc = as_utc_aware_for_route(ends_at_utc)
        now = get_utc_now_for_route()

        is_expired = (
            normalized_ends_at_utc is not None
            and normalized_ends_at_utc < now
        )

        available_plans = list_active_subscription_plans(db=db)

        return BusinessSubscriptionOverviewResponse(
            business=build_business_response(
                business,
                subscription=current_subscription,
                plan=current_plan,
            ),
            current_subscription=(
                build_business_subscription_response(current_subscription)
                if current_subscription is not None
                else None
            ),
            current_plan=(
                build_subscription_plan_response(current_plan)
                if current_plan is not None
                else None
            ),
            active_user_count=active_user_count,
            remaining_days=calculate_remaining_days(ends_at_utc),
            is_expired=is_expired,
            available_plans=[
                build_subscription_plan_response(plan)
                for plan in available_plans
            ],
        )
    except HTTPException:
        raise
    except AccessControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc


@router.post(
    "",
    response_model=BusinessWithOwnerCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_business_with_owner_endpoint(
    payload: CreateBusinessWithOwnerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessWithOwnerCreatedResponse:
    """Create a business, its first boss user, and default trial subscription."""

    try:
        result = create_business_with_owner(
            db=db,
            current_user=current_user,
            business_name=payload.business_name,
            business_slug=payload.business_slug,
            owner_full_name=payload.owner_full_name,
            owner_username=payload.owner_username,
            owner_password=payload.owner_password,
            business_owner_name=payload.business_owner_name,
            business_phone=payload.business_phone,
            business_email=payload.business_email,
            business_address=payload.business_address,
            owner_email=payload.owner_email,
            owner_role=payload.owner_role,
            timezone=payload.timezone,
            default_theme=payload.default_theme,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(result.business)
        db.refresh(result.owner_user)

        if result.subscription is not None:
            db.refresh(result.subscription)

        return BusinessWithOwnerCreatedResponse(
            business=build_business_response(result.business),
            owner_user=build_business_owner_user_response(result.owner_user),
            subscription=(
                build_business_subscription_response(result.subscription)
                if result.subscription is not None
                else None
            ),
            message="İşletme, ilk işletme sahibi ve deneme aboneliği oluşturuldu.",
        )
    except HTTPException:
        db.rollback()
        raise
    except DuplicateBusinessSlugError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu işletme kodu zaten kullanılıyor.",
        ) from exc
    except DuplicateUsernameError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu kullanıcı adı ilgili işletmede zaten kullanılıyor.",
        ) from exc
    except WeakPasswordError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Şifre güvenlik politikasına uygun değil.",
                "errors": exc.errors,
            },
        ) from exc
    except InvalidBusinessSlugError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidBusinessOwnerRoleError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İlk işletme sahibi rolü geçersiz.",
        ) from exc
    except SubscriptionPlanNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Varsayılan abonelik planı bulunamadı.",
        ) from exc
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except BusinessServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AuthServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kullanıcı oluşturma işlemi tamamlanamadı.",
        ) from exc
    except SubscriptionServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/{business_id}/subscription/extend",
    response_model=BusinessSubscriptionPlanChangedResponse,
)
def extend_business_subscription_endpoint(
    business_id: int,
    payload: ExtendBusinessSubscriptionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessSubscriptionPlanChangedResponse:
    """Extend current business subscription without changing its plan."""

    try:
        subscription = extend_business_subscription(
            db=db,
            current_user=current_user,
            business_id=business_id,
            duration_days=payload.duration_days,
            billing_period=payload.billing_period,
            notes=payload.notes,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(subscription)

        return BusinessSubscriptionPlanChangedResponse(
            subscription=build_business_subscription_response(subscription),
            message="İşletme abonelik süresi uzatıldı.",
        )
    except HTTPException:
        db.rollback()
        raise
    except BusinessNotFoundForSubscriptionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı.",
        ) from exc
    except BusinessSubscriptionNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme aboneliği bulunamadı.",
        ) from exc
    except SubscriptionPlanNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abonelik planı bulunamadı.",
        ) from exc
    except BusinessSubscriptionCannotBeExtendedError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except SubscriptionServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/{business_id}/subscription/status",
    response_model=BusinessSubscriptionPlanChangedResponse,
)
def update_business_subscription_status_endpoint(
    business_id: int,
    payload: UpdateBusinessSubscriptionStatusRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessSubscriptionPlanChangedResponse:
    """Suspend, reactivate or cancel current business subscription."""

    try:
        subscription = update_business_subscription_status(
            db=db,
            current_user=current_user,
            business_id=business_id,
            status=payload.status,
            notes=payload.notes,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(subscription)

        return BusinessSubscriptionPlanChangedResponse(
            subscription=build_business_subscription_response(subscription),
            message="İşletme abonelik durumu güncellendi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except BusinessNotFoundForSubscriptionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı.",
        ) from exc
    except BusinessSubscriptionNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme aboneliği bulunamadı.",
        ) from exc
    except SubscriptionPlanNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abonelik planı bulunamadı.",
        ) from exc
    except BusinessSubscriptionStatusUpdateError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except SubscriptionServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/{business_id}/subscription/change-plan",
    response_model=BusinessSubscriptionPlanChangedResponse,
)
def change_business_subscription_plan_endpoint(
    business_id: int,
    payload: ChangeBusinessPlanRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessSubscriptionPlanChangedResponse:
    """Change business plan without extending subscription duration."""

    try:
        subscription = change_business_plan(
            db=db,
            current_user=current_user,
            business_id=business_id,
            plan_code=payload.plan_code,
            preserve_remaining_time=payload.preserve_remaining_time,
            notes=payload.notes,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(subscription)

        return BusinessSubscriptionPlanChangedResponse(
            subscription=build_business_subscription_response(subscription),
            message="İşletme abonelik planı güncellendi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except BusinessNotFoundForSubscriptionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı.",
        ) from exc
    except BusinessSubscriptionNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme aboneliği bulunamadı.",
        ) from exc
    except SubscriptionPlanNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abonelik planı bulunamadı.",
        ) from exc
    except SubscriptionPlanUserLimitTooLowError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except BusinessSubscriptionCannotBeExtendedError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except SubscriptionServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise
