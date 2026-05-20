from __future__ import annotations

from datetime import time
import os

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.roles import UserRole
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.task import Task
from app.models.task_template import TaskTemplate
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.business_service import create_business_owner, create_business_with_owner
from app.services.task_service import (
    TASK_TYPE_EXTRA,
    create_extra_task,
    create_routine_task_template,
    generate_daily_routine_tasks,
    get_business_today,
)
from app.services.user_management_service import create_business_user


BUSINESS_NAME = "Missio Demo Market"
BUSINESS_SLUG = "missio-demo-market"

OWNER_FULL_NAME = "Demo Owner"
OWNER_USERNAME = "owner"
OWNER_PASSWORD = "Missio.2026!"
OWNER_EMAIL = "owner@missio.local"

MANAGER_FULL_NAME = "Demo Manager"
MANAGER_USERNAME = "manager"
MANAGER_PASSWORD = "Missio.2026!"
MANAGER_EMAIL = "manager@missio.local"

STAFF_FULL_NAME = "Ahmet Personel"
STAFF_USERNAME = "ahmet"
STAFF_PASSWORD = "Missio.2026!"
STAFF_EMAIL = "ahmet@missio.local"

SECOND_STAFF_FULL_NAME = "Ali Personel"
SECOND_STAFF_USERNAME = "ali"
SECOND_STAFF_PASSWORD = "Missio.2026!"
SECOND_STAFF_EMAIL = "ali@missio.local"



def ensure_demo_seed_is_allowed() -> None:
    """Ensure demo seed command is explicitly allowed."""

    allow_demo_seed = os.getenv("MISSIO_ALLOW_DEMO_SEED", "").strip()

    if allow_demo_seed != "1":
        raise RuntimeError(
            "Demo veri olu?turma komutu kilitli. "
            "Local geli?tirme ortam?nda ?al??t?rmak i?in ?nce ?u ortam de?i?kenini verin: "
            "PowerShell: $env:MISSIO_ALLOW_DEMO_SEED='1' "
            "Sonra: python -m app.commands.seed_local_task_demo_data"
        )


def get_super_admin(db) -> User:
    """Return active super admin user."""

    user = (
        db.execute(
            select(User)
            .where(
                User.role == UserRole.SUPER_ADMIN.value,
                User.is_active.is_(True),
            )
            .order_by(User.id.asc())
        )
        .scalars()
        .first()
    )

    if user is None:
        raise RuntimeError(
            "Aktif super_admin bulunamadı. Önce şu komutu çalıştırın: "
            "python -m app.commands.create_local_super_admin"
        )

    return user


def get_business_by_slug(db, *, slug: str) -> Business | None:
    """Return business by slug."""

    return (
        db.execute(select(Business).where(Business.slug == slug))
        .scalars()
        .first()
    )


def get_business_user_by_username(
    db,
    *,
    business_id: int,
    username: str,
) -> User | None:
    """Return business scoped user by username."""

    return (
        db.execute(
            select(User).where(
                User.business_id == business_id,
                User.username == normalize_username(username),
            )
        )
        .scalars()
        .first()
    )


def get_or_create_business_and_owner(
    db,
    *,
    super_admin: User,
) -> tuple[Business, User]:
    """Create demo business and owner if missing."""

    business = get_business_by_slug(db=db, slug=BUSINESS_SLUG)

    if business is None:
        result = create_business_with_owner(
            db=db,
            current_user=super_admin,
            business_name=BUSINESS_NAME,
            business_slug=BUSINESS_SLUG,
            owner_full_name=OWNER_FULL_NAME,
            owner_username=OWNER_USERNAME,
            owner_password=OWNER_PASSWORD,
            owner_email=OWNER_EMAIL,
            business_email="demo@missio.local",
            business_owner_name=OWNER_FULL_NAME,
            timezone="Europe/Istanbul",
            default_theme="dark",
            ip_address="127.0.0.1",
            user_agent="Missio local task demo seed command",
        )

        db.commit()
        db.refresh(result.business)
        db.refresh(result.owner_user)

        print(f"[OK] Demo işletme oluşturuldu: {result.business.name}")
        print(f"[OK] Demo owner oluşturuldu: {result.owner_user.username}")

        return result.business, result.owner_user

    owner = get_business_user_by_username(
        db=db,
        business_id=business.id,
        username=OWNER_USERNAME,
    )

    if owner is None:
        owner = create_business_owner(
            db=db,
            current_user=super_admin,
            business=business,
            full_name=OWNER_FULL_NAME,
            username=OWNER_USERNAME,
            password=OWNER_PASSWORD,
            email=OWNER_EMAIL,
            role=UserRole.BOSS.value,
            ip_address="127.0.0.1",
            user_agent="Missio local task demo seed command",
        )

        db.commit()
        db.refresh(owner)

        print(f"[OK] Eksik demo owner oluşturuldu: {owner.username}")
    else:
        print(f"[INFO] Demo işletme zaten var: {business.name}")
        print(f"[INFO] Demo owner zaten var: {owner.username}")

    return business, owner


def get_or_create_business_user(
    db,
    *,
    owner: User,
    business: Business,
    full_name: str,
    username: str,
    password: str,
    email: str,
    role: str,
) -> User:
    """Create demo manager/staff user if missing."""

    user = get_business_user_by_username(
        db=db,
        business_id=business.id,
        username=username,
    )

    if user is not None:
        user.is_active = True
        user.role = role
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"[INFO] Kullanıcı zaten var: {user.username} ({user.role})")
        return user

    user = create_business_user(
        db=db,
        current_user=owner,
        business=business,
        full_name=full_name,
        username=username,
        password=password,
        role=role,
        email=email,
        ip_address="127.0.0.1",
        user_agent="Missio local task demo seed command",
    )

    db.commit()
    db.refresh(user)

    print(f"[OK] Kullanıcı oluşturuldu: {user.username} ({user.role})")

    return user


def routine_template_exists(
    db,
    *,
    business_id: int,
    assigned_to_user_id: int,
    title: str,
) -> bool:
    """Return whether routine template already exists."""

    template = (
        db.execute(
            select(TaskTemplate).where(
                TaskTemplate.business_id == business_id,
                TaskTemplate.assigned_to_user_id == assigned_to_user_id,
                TaskTemplate.title == title,
            )
        )
        .scalars()
        .first()
    )

    return template is not None


def create_routine_template_if_missing(
    db,
    *,
    owner: User,
    business: Business,
    assigned_to_user: User,
    title: str,
    description: str | None = None,
    due_time: time | None = None,
    requires_photo: bool = False,
    requires_manager_approval: bool = False,
) -> None:
    """Create routine template if missing."""

    if routine_template_exists(
        db=db,
        business_id=business.id,
        assigned_to_user_id=assigned_to_user.id,
        title=title,
    ):
        print(f"[INFO] Rutin görev zaten var: {assigned_to_user.username} -> {title}")
        return

    template = create_routine_task_template(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=assigned_to_user,
        title=title,
        description=description,
        default_due_time_local=due_time,
        requires_photo=requires_photo,
        requires_location=False,
        requires_manager_approval=requires_manager_approval,
    )

    db.commit()
    db.refresh(template)

    print(f"[OK] Rutin görev eklendi: {assigned_to_user.username} -> {template.title}")


def extra_task_exists(
    db,
    *,
    business_id: int,
    assigned_to_user_id: int,
    task_date,
    title: str,
) -> bool:
    """Return whether extra task already exists for selected day."""

    task = (
        db.execute(
            select(Task).where(
                Task.business_id == business_id,
                Task.assigned_to_user_id == assigned_to_user_id,
                Task.task_type == TASK_TYPE_EXTRA,
                Task.task_date == task_date,
                Task.title == title,
                Task.deleted_at_utc.is_(None),
            )
        )
        .scalars()
        .first()
    )

    return task is not None


def create_extra_task_if_missing(
    db,
    *,
    owner: User,
    business: Business,
    assigned_to_user: User,
    title: str,
    description: str | None = None,
    requires_photo: bool = False,
) -> None:
    """Create extra task if missing for today."""

    task_date = get_business_today(business)

    if extra_task_exists(
        db=db,
        business_id=business.id,
        assigned_to_user_id=assigned_to_user.id,
        task_date=task_date,
        title=title,
    ):
        print(f"[INFO] Ekstra görev zaten var: {assigned_to_user.username} -> {title}")
        return

    task = create_extra_task(
        db=db,
        current_user=owner,
        business=business,
        assigned_to_user=assigned_to_user,
        title=title,
        description=description,
        requires_photo=requires_photo,
        requires_location=False,
        requires_manager_approval=False,
        ip_address="127.0.0.1",
        user_agent="Missio local task demo seed command",
    )

    db.commit()
    db.refresh(task)

    print(f"[OK] Ekstra görev eklendi: {assigned_to_user.username} -> {task.title}")


def main() -> None:
    """Seed local task demo data."""

    ensure_demo_seed_is_allowed()

    db = SessionLocal()

    try:
        super_admin = get_super_admin(db)

        business, owner = get_or_create_business_and_owner(
            db=db,
            super_admin=super_admin,
        )

        manager = get_or_create_business_user(
            db=db,
            owner=owner,
            business=business,
            full_name=MANAGER_FULL_NAME,
            username=MANAGER_USERNAME,
            password=MANAGER_PASSWORD,
            email=MANAGER_EMAIL,
            role=UserRole.MANAGER.value,
        )

        staff = get_or_create_business_user(
            db=db,
            owner=owner,
            business=business,
            full_name=STAFF_FULL_NAME,
            username=STAFF_USERNAME,
            password=STAFF_PASSWORD,
            email=STAFF_EMAIL,
            role=UserRole.STAFF.value,
        )

        second_staff = get_or_create_business_user(
            db=db,
            owner=owner,
            business=business,
            full_name=SECOND_STAFF_FULL_NAME,
            username=SECOND_STAFF_USERNAME,
            password=SECOND_STAFF_PASSWORD,
            email=SECOND_STAFF_EMAIL,
            role=UserRole.STAFF.value,
        )

        create_routine_template_if_missing(
            db=db,
            owner=owner,
            business=business,
            assigned_to_user=staff,
            title="Raf temizlik",
            description="Sorumlu olduğu rafların günlük temizlik kontrolü.",
            due_time=time(hour=10, minute=0),
            requires_photo=True,
            requires_manager_approval=True,
        )

        create_routine_template_if_missing(
            db=db,
            owner=owner,
            business=business,
            assigned_to_user=staff,
            title="Tarih kontrolü",
            description="Raflardaki ürünlerin son kullanma tarihi kontrolü.",
            due_time=time(hour=11, minute=0),
            requires_photo=False,
            requires_manager_approval=True,
        )

        create_routine_template_if_missing(
            db=db,
            owner=owner,
            business=business,
            assigned_to_user=staff,
            title="Eksik ürün tespiti",
            description="Eksik ürünlerin tespiti ve manager'a bildirilmesi.",
            due_time=time(hour=12, minute=0),
            requires_photo=False,
            requires_manager_approval=False,
        )

        create_routine_template_if_missing(
            db=db,
            owner=owner,
            business=business,
            assigned_to_user=second_staff,
            title="Depo düzenleme",
            description="Depo geçiş alanlarının günlük düzen kontrolü.",
            due_time=time(hour=16, minute=0),
            requires_photo=True,
            requires_manager_approval=True,
        )

        create_routine_template_if_missing(
            db=db,
            owner=owner,
            business=business,
            assigned_to_user=manager,
            title="Gün sonu personel görev kontrolü",
            description="Personellerin tamamlamadığı görevlerin gün sonu kontrolü.",
            due_time=time(hour=21, minute=0),
            requires_photo=False,
            requires_manager_approval=False,
        )

        create_extra_task_if_missing(
            db=db,
            owner=owner,
            business=business,
            assigned_to_user=staff,
            title="Raftaki Ülker marka çikolatalar sayılsın",
            description="Ülker çikolata ürünlerinin raf sayımı yapılsın.",
            requires_photo=False,
        )

        create_extra_task_if_missing(
            db=db,
            owner=owner,
            business=business,
            assigned_to_user=second_staff,
            title="Eti bisküviler bir üst rafa taşınsın",
            description="Eti bisküvi ürünleri bir üst rafa taşınsın ve raf düzeni kontrol edilsin.",
            requires_photo=True,
        )

        generation_result = generate_daily_routine_tasks(
            db=db,
            current_user=owner,
            business=business,
            task_date=None,
            assigned_to_user_id=None,
            ip_address="127.0.0.1",
            user_agent="Missio local task demo seed command",
        )

        db.commit()

        print("")
        print("[OK] Demo görev verisi hazırlandı.")
        print(f"[OK] İşletme: {business.name} | business_id={business.id}")
        print(f"[OK] Owner: username={owner.username} | password={OWNER_PASSWORD}")
        print(f"[OK] Manager: username={manager.username} | password={MANAGER_PASSWORD}")
        print(f"[OK] Staff 1: username={staff.username} | password={STAFF_PASSWORD}")
        print(f"[OK] Staff 2: username={second_staff.username} | password={SECOND_STAFF_PASSWORD}")
        print(
            "[OK] Bugünkü rutin üretim: "
            f"created={generation_result.created_count}, "
            f"skipped={generation_result.skipped_count}, "
            f"task_date={generation_result.task_date}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()