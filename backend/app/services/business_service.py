from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.business import Business
from app.models.user import User
from app.repositories.business_repository import add_business, is_business_slug_taken
from app.services.access_control_service import require_roles
from app.services.audit_log_service import create_audit_log
from app.services.auth_service import create_user_with_password


class BusinessServiceError(ValueError):
    """Base error for business service failures."""


class DuplicateBusinessSlugError(BusinessServiceError):
    """Raised when business slug already exists."""


class InvalidBusinessSlugError(BusinessServiceError):
    """Raised when business slug is invalid."""


class InvalidBusinessOwnerRoleError(BusinessServiceError):
    """Raised when owner role is not allowed."""


ALLOWED_OWNER_ROLES = {
    UserRole.BOSS.value,
}


@dataclass(frozen=True)
class BusinessWithOwner:
    """Created business and its first owner user."""

    business: Business
    owner_user: User


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def normalize_business_slug(value: str) -> str:
    """Normalize business slug with Turkish character and Unicode mark handling."""

    lowered = value.strip().lower()
    translation_table = str.maketrans(
        {
            "ı": "i",
            "ğ": "g",
            "ü": "u",
            "ş": "s",
            "ö": "o",
            "ç": "c",
        }
    )
    translated = lowered.translate(translation_table)
    decomposed = unicodedata.normalize("NFKD", translated)
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    normalized = re.sub(r"[^a-z0-9]+", "-", without_marks)
    normalized = normalized.strip("-")

    return normalized

def validate_business_slug(slug: str) -> None:
    """Validate normalized business slug."""

    if not slug:
        raise InvalidBusinessSlugError("İşletme slug boş olamaz.")

    if len(slug) < 3:
        raise InvalidBusinessSlugError("İşletme slug en az 3 karakter olmalıdır.")

    if len(slug) > 120:
        raise InvalidBusinessSlugError("İşletme slug en fazla 120 karakter olabilir.")

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise InvalidBusinessSlugError("İşletme slug formatı geçersiz.")


def create_business(
    db: Session,
    *,
    current_user: User,
    name: str,
    slug: str,
    owner_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    timezone: str = "Europe/Istanbul",
    default_theme: str = "dark",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Business:
    """Create a business as super admin."""

    require_roles(current_user, [UserRole.SUPER_ADMIN])

    normalized_name = name.strip()

    if not normalized_name:
        raise BusinessServiceError("İşletme adı boş olamaz.")

    normalized_slug = normalize_business_slug(slug)
    validate_business_slug(normalized_slug)

    if is_business_slug_taken(db=db, slug=normalized_slug):
        raise DuplicateBusinessSlugError("Bu işletme slug değeri zaten kullanılıyor.")

    now = get_utc_now()
    business = Business(
        name=normalized_name,
        slug=normalized_slug,
        logo_path=None,
        owner_name=owner_name.strip() if owner_name else None,
        phone=phone.strip() if phone else None,
        email=email.strip().lower() if email else None,
        address=address.strip() if address else None,
        timezone=timezone.strip() or "Europe/Istanbul",
        default_theme=default_theme.strip() or "dark",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    business = add_business(db=db, business=business)

    create_audit_log(
        db=db,
        action="business.created",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="business",
        entity_id=str(business.id),
        detail={
            "business_id": business.id,
            "name": business.name,
            "slug": business.slug,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return business


def create_business_owner(
    db: Session,
    *,
    current_user: User,
    business: Business,
    full_name: str,
    username: str,
    password: str,
    email: str | None = None,
    role: str = UserRole.BOSS.value,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    """Create first owner user for a business as super admin."""

    require_roles(current_user, [UserRole.SUPER_ADMIN])

    if role not in ALLOWED_OWNER_ROLES:
        raise InvalidBusinessOwnerRoleError("İşletme sahibi rolü geçersiz.")

    owner_user = create_user_with_password(
        db=db,
        full_name=full_name,
        username=username,
        password=password,
        role=role,
        business_id=business.id,
        email=email,
        is_active=True,
    )

    create_audit_log(
        db=db,
        action="business.owner_created",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="user",
        entity_id=str(owner_user.id),
        detail={
            "business_id": business.id,
            "owner_user_id": owner_user.id,
            "username": owner_user.username,
            "role": owner_user.role,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return owner_user


def create_business_with_owner(
    db: Session,
    *,
    current_user: User,
    business_name: str,
    business_slug: str,
    owner_full_name: str,
    owner_username: str,
    owner_password: str,
    business_owner_name: str | None = None,
    business_phone: str | None = None,
    business_email: str | None = None,
    business_address: str | None = None,
    owner_email: str | None = None,
    owner_role: str = UserRole.BOSS.value,
    timezone: str = "Europe/Istanbul",
    default_theme: str = "dark",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> BusinessWithOwner:
    """Create business and first owner user in one transaction scope."""

    business = create_business(
        db=db,
        current_user=current_user,
        name=business_name,
        slug=business_slug,
        owner_name=business_owner_name or owner_full_name,
        phone=business_phone,
        email=business_email,
        address=business_address,
        timezone=timezone,
        default_theme=default_theme,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    owner_user = create_business_owner(
        db=db,
        current_user=current_user,
        business=business,
        full_name=owner_full_name,
        username=owner_username,
        password=owner_password,
        email=owner_email,
        role=owner_role,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return BusinessWithOwner(business=business, owner_user=owner_user)
