from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.roles import UserRole
from app.core.security import hash_password, validate_password_strength
from app.db.session import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.business_user import (
    BusinessUserCreatedResponse,
    BusinessUserPasswordResetResponse,
    BusinessUserResponse,
    BusinessUserRoleChangedResponse,
    BusinessUserUpdatedResponse,
    ChangeBusinessUserRoleRequest,
    CreateBusinessUserRequest,
    ResetBusinessUserPasswordRequest,
    UpdateBusinessUserRequest,
)
from app.services.access_control_service import (
    AccessControlError,
    ensure_business_user_management_access,
)
from app.services.audit_log_service import create_audit_log
from app.services.auth_service import (
    AuthServiceError,
    DuplicateUsernameError,
    WeakPasswordError,
)
from app.services.user_management_service import (
    BusinessUserManagementError,
    InvalidBusinessUserRoleError,
    InvalidBusinessUserSupervisorError,
    create_business_user,
    resolve_business_user_supervisor,
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


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


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


def ensure_can_update_business_user(current_user: User, target_user: User) -> None:
    """Ensure current user can update target business user."""

    if current_user.role == UserRole.SUPER_ADMIN.value:
        return

    if current_user.role in {
        UserRole.BOSS.value,
        }:
        if target_user.role in {
            UserRole.MANAGER.value,
            UserRole.STAFF.value,
        }:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kullanıcıyı güncelleme yetkiniz yok.",
        )

    if current_user.role == UserRole.MANAGER.value:
        if target_user.role == UserRole.STAFF.value:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager sadece personel kullanıcısını güncelleyebilir.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bu işlem için yetkiniz yok.",
    )


def ensure_can_reset_business_user_password(
    current_user: User,
    target_user: User,
) -> None:
    """Ensure current user can reset target business user's password."""

    if current_user.role == UserRole.SUPER_ADMIN.value:
        return

    if current_user.role in {
        UserRole.BOSS.value,
        }:
        if target_user.role in {
            UserRole.MANAGER.value,
            UserRole.STAFF.value,
        }:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kullanıcının şifresini sıfırlama yetkiniz yok.",
        )

    if current_user.role == UserRole.MANAGER.value:
        if target_user.role == UserRole.STAFF.value:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager sadece personel kullanıcısının şifresini sıfırlayabilir.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bu işlem için yetkiniz yok.",
    )


def ensure_can_change_business_user_role(
    current_user: User,
    target_user: User,
    new_role: str,
) -> None:
    """Ensure current user can change target business user's role safely."""

    allowed_change_roles = {
        UserRole.MANAGER.value,
        UserRole.STAFF.value,
    }

    if target_user.role not in allowed_change_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kullanıcının rolü bu endpoint üzerinden değiştirilemez.",
        )

    if new_role not in allowed_change_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol değişikliği sadece manager veya staff için yapılabilir.",
        )

    if target_user.role == new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kullanıcı zaten bu role sahip.",
        )

    if current_user.role == UserRole.SUPER_ADMIN.value:
        return

    if current_user.role in {
        UserRole.BOSS.value,
        }:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bu işlem için yetkiniz yok.",
    )


def get_business_user_supervisor_for_response(
    db: Session,
    user: User,
) -> User | None:
    """Return supervisor user for response payload if available."""

    if user.supervisor_user_id is None:
        return None

    supervisor_user = db.get(User, user.supervisor_user_id)

    if supervisor_user is None:
        return None

    if supervisor_user.business_id != user.business_id:
        return None

    return supervisor_user


def ensure_can_update_business_user_supervisor(current_user: User) -> None:
    """Only super admin and boss can change staff supervisor assignments."""

    if current_user.role in {
        UserRole.SUPER_ADMIN.value,
        UserRole.BOSS.value,
    }:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sorumlu yönetici bilgisini değiştirme yetkiniz yok.",
    )


def build_business_user_response(user: User, *, db: Session) -> BusinessUserResponse:
    """Build safe business user response."""

    if user.business_id is None:
        raise RuntimeError("Business user response business_id boş olamaz.")

    supervisor_user = get_business_user_supervisor_for_response(db=db, user=user)

    return BusinessUserResponse(
        id=user.id,
        business_id=user.business_id,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        role=user.role,
        supervisor_user_id=user.supervisor_user_id,
        supervisor_full_name=supervisor_user.full_name if supervisor_user is not None else None,
        supervisor_username=supervisor_user.username if supervisor_user is not None else None,
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
            supervisor_user_id=payload.supervisor_user_id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        db.commit()
        db.refresh(user)

        return BusinessUserCreatedResponse(
            user=build_business_user_response(user, db=db),
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
    except InvalidBusinessUserSupervisorError as exc:
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

        return [build_business_user_response(user, db=db) for user in users]
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

        return build_business_user_response(user, db=db)
    except HTTPException:
        raise
    except AccessControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc


@router.patch(
    "/{business_id}/users/{user_id}",
    response_model=BusinessUserUpdatedResponse,
)
def update_business_user_endpoint(
    business_id: int,
    user_id: int,
    payload: UpdateBusinessUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessUserUpdatedResponse:
    """Update a business scoped user according to the permission matrix."""

    try:
        business = get_business_or_404(db=db, business_id=business_id)

        ensure_business_user_management_access(
            current_user=current_user,
            target_business_id=business.id,
        )

        user = get_business_user_or_404(db=db, user_id=user_id)
        ensure_user_belongs_to_business(user=user, business_id=business.id)
        ensure_can_update_business_user(
            current_user=current_user,
            target_user=user,
        )

        update_fields = payload.model_fields_set

        if "full_name" in update_fields:
            if payload.full_name is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Ad soyad boş olamaz.",
                )

            user.full_name = payload.full_name

        if "email" in update_fields:
            user.email = payload.email

        if "theme_preference" in update_fields:
            user.theme_preference = payload.theme_preference

        if "supervisor_user_id" in update_fields:
            ensure_can_update_business_user_supervisor(current_user)
            supervisor_user = resolve_business_user_supervisor(
                db=db,
                business=business,
                target_role=user.role,
                supervisor_user_id=payload.supervisor_user_id,
            )
            user.supervisor_user_id = (
                supervisor_user.id if supervisor_user is not None else None
            )

        if "is_active" in update_fields:
            if user.id == current_user.id and payload.is_active is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Kendi kullanıcınızı pasif hale getiremezsiniz.",
                )

            if payload.is_active is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="is_active boş olamaz.",
                )

            user.is_active = payload.is_active

        user.updated_at = get_utc_now()

        create_audit_log(
            db=db,
            action="business.user_updated",
            business_id=business.id,
            user_id=current_user.id,
            entity_type="user",
            entity_id=str(user.id),
            detail={
                "business_id": business.id,
                "updated_user_id": user.id,
                "updated_username": user.username,
                "updated_user_role": user.role,
                "updated_fields": sorted(update_fields),
                "updated_by_user_id": current_user.id,
                "updated_by_role": current_user.role,
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return BusinessUserUpdatedResponse(
            user=build_business_user_response(user, db=db),
            message="İşletme kullanıcısı güncellendi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except InvalidBusinessUserSupervisorError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/{business_id}/users/{user_id}/reset-password",
    response_model=BusinessUserPasswordResetResponse,
)
def reset_business_user_password_endpoint(
    business_id: int,
    user_id: int,
    payload: ResetBusinessUserPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessUserPasswordResetResponse:
    """Reset a business scoped user's password according to the permission matrix."""

    try:
        business = get_business_or_404(db=db, business_id=business_id)

        ensure_business_user_management_access(
            current_user=current_user,
            target_business_id=business.id,
        )

        user = get_business_user_or_404(db=db, user_id=user_id)
        ensure_user_belongs_to_business(user=user, business_id=business.id)
        ensure_can_reset_business_user_password(
            current_user=current_user,
            target_user=user,
        )

        password_errors = validate_password_strength(payload.new_password)

        if password_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Şifre güvenlik politikasına uygun değil.",
                    "errors": password_errors,
                },
            )

        user.password_hash = hash_password(payload.new_password)
        user.updated_at = get_utc_now()

        create_audit_log(
            db=db,
            action="business.user_password_reset",
            business_id=business.id,
            user_id=current_user.id,
            entity_type="user",
            entity_id=str(user.id),
            detail={
                "business_id": business.id,
                "password_reset_user_id": user.id,
                "password_reset_username": user.username,
                "password_reset_user_role": user.role,
                "password_reset_by_user_id": current_user.id,
                "password_reset_by_role": current_user.role,
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return BusinessUserPasswordResetResponse(
            user=build_business_user_response(user, db=db),
            message="İşletme kullanıcısı şifresi sıfırlandı.",
        )
    except HTTPException:
        db.rollback()
        raise
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/{business_id}/users/{user_id}/change-role",
    response_model=BusinessUserRoleChangedResponse,
)
def change_business_user_role_endpoint(
    business_id: int,
    user_id: int,
    payload: ChangeBusinessUserRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessUserRoleChangedResponse:
    """Change a business scoped user's role according to the permission matrix."""

    try:
        business = get_business_or_404(db=db, business_id=business_id)

        ensure_business_user_management_access(
            current_user=current_user,
            target_business_id=business.id,
        )

        user = get_business_user_or_404(db=db, user_id=user_id)
        ensure_user_belongs_to_business(user=user, business_id=business.id)

        old_role = user.role

        ensure_can_change_business_user_role(
            current_user=current_user,
            target_user=user,
            new_role=payload.role,
        )

        user.role = payload.role
        if user.role != UserRole.STAFF.value:
            user.supervisor_user_id = None
        user.updated_at = get_utc_now()

        create_audit_log(
            db=db,
            action="business.user_role_changed",
            business_id=business.id,
            user_id=current_user.id,
            entity_type="user",
            entity_id=str(user.id),
            detail={
                "business_id": business.id,
                "role_changed_user_id": user.id,
                "role_changed_username": user.username,
                "old_role": old_role,
                "new_role": user.role,
                "changed_by_user_id": current_user.id,
                "changed_by_role": current_user.role,
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return BusinessUserRoleChangedResponse(
            user=build_business_user_response(user, db=db),
            message="İşletme kullanıcısı rolü güncellendi.",
        )
    except HTTPException:
        db.rollback()
        raise
    except AccessControlError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        ) from exc
    except Exception:
        db.rollback()
        raise