from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.roles import UserRole
from app.db.session import get_db
from app.models.business import Business
from app.models.business_subscription import BusinessSubscription
from app.models.user import User
from app.schemas.business import (
    BusinessOwnerUserResponse,
    BusinessResponse,
    BusinessSubscriptionResponse,
    BusinessWithOwnerCreatedResponse,
    CreateBusinessWithOwnerRequest,
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
    SubscriptionPlanNotFoundError,
    SubscriptionServiceError,
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


def build_business_response(business: Business) -> BusinessResponse:
    """Build safe business response."""

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


@router.get("", response_model=list[BusinessResponse])
def list_businesses_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BusinessResponse]:
    """List all businesses for super admin panel."""

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

        return [build_business_response(business) for business in businesses]
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
