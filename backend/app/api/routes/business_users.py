from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.business_user import (
    BusinessUserCreatedResponse,
    BusinessUserResponse,
    CreateBusinessUserRequest,
)
from app.services.access_control_service import (
    AccessControlError,
    ensure_business_user_management_access,
)
from app.services.auth_service import (
    AuthServiceError,
    DuplicateUsernameError,
    WeakPasswordError,
)
from app.services.user_management_service import (
    BusinessUserManagementError,
    InvalidBusinessUserRoleError,
    create_business_user,
)


router = APIRouter(prefix="/businesses", tags=["business-users"])


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


def get_business_or_404(db: Session, business_id: int) -> Business:
    """Return business by id or raise 404."""

    business = db.get(Business, business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı.",
        )

    return business


def get_business_user_or_404(db: Session, user_id: int) -> User:
    """Return user by id or raise 404."""

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı.",
        )

    return user


def ensure_user_belongs_to_business(user: User, business_id: int) -> None:
    """Ensure user record belongs to the requested business."""

    if user.business_id != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kullanıcıya erişim yetkiniz yok.",
        )


def build_business_user_response(user: User) -> BusinessUserResponse:
    """Build safe business user response."""

    if user.business_id is None:
        raise RuntimeError("Business user response business_id boş olamaz.")

    return BusinessUserResponse(
        id=user.id,
        business_id=user.business_id,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        theme_preference=user.theme_preference,
    )


@router.post(
    "/{business_id}/users",
    response_model=BusinessUserCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_business_user_endpoint(
    business_id: int,
    payload: CreateBusinessUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessUserCreatedResponse:
    """Create a business scoped user according to the permission matrix."""

    try:
        business = get_business_or_404(db=db, business_id=business_id)

        user = create_business_user(
            db=db,
            current_user=current_user,
            business=business,
            full_name=payload.full_name,
            username=payload.username,
            password=payload.password,
            role=payload.role,
            email=payload.email,
            theme_preference=payload.theme_preference,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        db.commit()
        db.refresh(user)

        return BusinessUserCreatedResponse(
            user=build_business_user_response(user),
            message="İşletme kullanıcısı oluşturuldu.",
        )
    except HTTPException:
        db.rollback()
        raise
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
    except InvalidBusinessUserRoleError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İşletme kullanıcısı rolü geçersiz.",
        ) from exc
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except BusinessUserManagementError as exc:
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
    except Exception:
        db.rollback()
        raise


@router.get(
    "/{business_id}/users",
    response_model=list[BusinessUserResponse],
)
def list_business_users_endpoint(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BusinessUserResponse]:
    """List users of a business according to the permission matrix."""

    try:
        business = get_business_or_404(db=db, business_id=business_id)

        ensure_business_user_management_access(
            current_user=current_user,
            target_business_id=business.id,
        )

        users = (
            db.execute(
                select(User)
                .where(User.business_id == business.id)
                .order_by(User.id.asc())
            )
            .scalars()
            .all()
        )

        return [build_business_user_response(user) for user in users]
    except HTTPException:
        raise
    except AccessControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc


@router.get(
    "/{business_id}/users/{user_id}",
    response_model=BusinessUserResponse,
)
def get_business_user_detail_endpoint(
    business_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessUserResponse:
    """Return a business user detail according to the permission matrix."""

    try:
        business = get_business_or_404(db=db, business_id=business_id)

        ensure_business_user_management_access(
            current_user=current_user,
            target_business_id=business.id,
        )

        user = get_business_user_or_404(db=db, user_id=user_id)
        ensure_user_belongs_to_business(user=user, business_id=business.id)

        return build_business_user_response(user)
    except HTTPException:
        raise
    except AccessControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc