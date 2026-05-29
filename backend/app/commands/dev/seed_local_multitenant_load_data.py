from __future__ import annotations

import argparse
import os
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.config import settings
from app.core.roles import UserRole
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.subscription_plan import SubscriptionPlan
from app.models.task import Task
from app.models.task_template import TaskTemplate
from app.models.user import User
from app.services.business_service import create_business_with_owner
from app.services.task_service import (
    TASK_TYPE_EXTRA,
    create_extra_task,
    create_routine_task_template,
    generate_daily_routine_tasks,
    get_business_today,
)
from app.services.user_management_service import create_business_user


DEFAULT_PASSWORD = "MissioLoad.2026!"
DEFAULT_BUSINESS_COUNT = 12
DEFAULT_MANAGER_COUNT = 2
DEFAULT_STAFF_COUNT = 10
DEFAULT_ROUTINE_PER_USER = 5
DEFAULT_EXTRA_PER_USER = 5


ROUTINE_TASK_TITLES = [
    "Açılış alan kontrolü",
    "Raf düzen kontrolü",
    "Eksik ürün kontrolü",
    "Temizlik kontrolü",
    "Gün ortası operasyon kontrolü",
]

EXTRA_TASK_TITLES = [
    "Fiyat etiketi kontrolü",
    "Ön vitrin düzenleme",
    "Depo geçiş alanı kontrolü",
    "Kasa çevresi düzenleme",
    "Müşteri alanı hızlı kontrol",
]


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_seed_is_allowed(*, force: bool) -> None:
    allow_seed = os.getenv("MISSIO_ALLOW_LOCAL_LOAD_TEST_SEED", "").strip()
    confirm = os.getenv("MISSIO_LOCAL_LOAD_TEST_CONFIRM", "").strip()
    environment = settings.environment.strip().lower()
    database_url = settings.database_url.strip().lower()

    allowed_environments = {"local", "dev", "development", "test", "testing"}

    if allow_seed != "1":
        raise RuntimeError(
            "Load test veri üretimi kilitli.\n"
            "PowerShell:\n"
            "$env:MISSIO_ALLOW_LOCAL_LOAD_TEST_SEED='1'\n"
            "$env:MISSIO_LOCAL_LOAD_TEST_CONFIRM='LOCAL_LOAD_TEST'\n"
        )

    if confirm != "LOCAL_LOAD_TEST":
        raise RuntimeError(
            "Onay anahtarı eksik.\n"
            "PowerShell:\n"
            "$env:MISSIO_LOCAL_LOAD_TEST_CONFIRM='LOCAL_LOAD_TEST'\n"
        )

    if environment not in allowed_environments and not force:
        raise RuntimeError(
            f"MISSIO_ENVIRONMENT='{settings.environment}' görünüyor.\n"
            "Bu komut varsayılan olarak sadece local/dev/test ortamlarında çalışır.\n"
            "Gerçekten lokal test verisi ürettiğinden eminsen --force parametresi kullanılabilir."
        )

    blocked_markers = [
        "cloudsql",
        "run.app",
        "googleusercontent",
        "europe-west1",
        "project-ac8ae551",
    ]

    if any(marker in database_url for marker in blocked_markers) and not force:
        raise RuntimeError(
            "DATABASE_URL canlı/Cloud SQL ortamına benziyor. İşlem durduruldu.\n"
            "Bu komut canlı veritabanında çalıştırılmamalıdır."
        )


def get_active_super_admin(db) -> User:
    super_admin = (
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

    if super_admin is None:
        raise RuntimeError(
            "Aktif super_admin bulunamadı.\n"
            "Önce lokal super admin oluştur:\n"
            "python -m app.commands.create_local_super_admin"
        )

    return super_admin


def ensure_trial_plan(db) -> SubscriptionPlan:
    now = get_utc_now()

    plan = (
        db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == "trial"))
        .scalars()
        .first()
    )

    if plan is None:
        plan = SubscriptionPlan(
            code="trial",
            name="Deneme",
            description="Local load test için otomatik oluşturulan deneme planı.",
            max_users=50,
            max_managers=15,
            max_daily_tasks=5000,
            report_retention_days=60,
            price_monthly=None,
            price_yearly=None,
            currency="TRY",
            display_order=1,
            is_active=True,
            created_at_utc=now,
            updated_at_utc=now,
        )
        db.add(plan)
        db.flush()
        return plan

    changed = False

    if plan.max_users < 50:
        plan.max_users = 50
        changed = True

    if plan.max_managers is None or plan.max_managers < 15:
        plan.max_managers = 15
        changed = True

    if plan.max_daily_tasks is None or plan.max_daily_tasks < 5000:
        plan.max_daily_tasks = 5000
        changed = True

    if not plan.is_active:
        plan.is_active = True
        changed = True

    if changed:
        plan.updated_at_utc = now
        db.add(plan)
        db.flush()

    return plan


def business_exists(db, *, slug: str) -> bool:
    existing = db.execute(select(Business.id).where(Business.slug == slug)).first()
    return existing is not None


def task_template_exists(
    db,
    *,
    business_id: int,
    assigned_to_user_id: int,
    title: str,
) -> bool:
    existing = (
        db.execute(
            select(TaskTemplate.id).where(
                TaskTemplate.business_id == business_id,
                TaskTemplate.assigned_to_user_id == assigned_to_user_id,
                TaskTemplate.title == title,
            )
        )
        .first()
    )

    return existing is not None


def extra_task_exists(
    db,
    *,
    business_id: int,
    assigned_to_user_id: int,
    title: str,
) -> bool:
    task_date = get_business_today(db.get(Business, business_id))

    existing = (
        db.execute(
            select(Task.id).where(
                Task.business_id == business_id,
                Task.assigned_to_user_id == assigned_to_user_id,
                Task.task_type == TASK_TYPE_EXTRA,
                Task.task_date == task_date,
                Task.title == title,
                Task.deleted_at_utc.is_(None),
            )
        )
        .first()
    )

    return existing is not None


def create_business_block(
    db,
    *,
    super_admin: User,
    run_id: str,
    business_index: int,
    manager_count: int,
    staff_count: int,
    routine_per_user: int,
    extra_per_user: int,
    password: str,
) -> dict[str, int]:
    business_no = f"{business_index:03d}"
    business_name = f"Load Test İşletme {business_no}"
    business_slug = f"load-test-{run_id}-{business_no}"

    if business_exists(db, slug=business_slug):
        raise RuntimeError(f"Bu run için işletme zaten var: {business_slug}")

    owner_username = f"boss{business_no}"
    owner_email = f"{owner_username}.{run_id}@missio.local"

    result = create_business_with_owner(
        db=db,
        current_user=super_admin,
        business_name=business_name,
        business_slug=business_slug,
        business_owner_name=f"Load Test Patron {business_no}",
        business_phone=f"+90533000{business_no}",
        business_email=f"business{business_no}.{run_id}@missio.local",
        business_address=f"Load test adresi {business_no}",
        owner_full_name=f"Load Test Patron {business_no}",
        owner_username=owner_username,
        owner_password=password,
        owner_email=owner_email,
        owner_role=UserRole.BOSS.value,
        timezone="Asia/Nicosia",
        default_theme="dark",
        ip_address="127.0.0.1",
        user_agent="Missio local multitenant load seed",
    )

    business = result.business
    owner = result.owner_user

    assignable_users: list[User] = []
    created_user_count = 1

    for manager_index in range(1, manager_count + 1):
        username = f"manager{business_no}{manager_index:02d}"
        user = create_business_user(
            db=db,
            current_user=owner,
            business=business,
            full_name=f"Load Test Yönetici {business_no}-{manager_index:02d}",
            username=username,
            password=password,
            role=UserRole.MANAGER.value,
            email=f"{username}.{run_id}@missio.local",
            ip_address="127.0.0.1",
            user_agent="Missio local multitenant load seed",
        )
        assignable_users.append(user)
        created_user_count += 1

    for staff_index in range(1, staff_count + 1):
        username = f"staff{business_no}{staff_index:02d}"
        user = create_business_user(
            db=db,
            current_user=owner,
            business=business,
            full_name=f"Load Test Personel {business_no}-{staff_index:02d}",
            username=username,
            password=password,
            role=UserRole.STAFF.value,
            email=f"{username}.{run_id}@missio.local",
            ip_address="127.0.0.1",
            user_agent="Missio local multitenant load seed",
        )
        assignable_users.append(user)
        created_user_count += 1

    created_template_count = 0
    created_extra_task_count = 0

    for user_index, assigned_user in enumerate(assignable_users, start=1):
        for routine_index in range(1, routine_per_user + 1):
            title_base = ROUTINE_TASK_TITLES[(routine_index - 1) % len(ROUTINE_TASK_TITLES)]
            title = f"{title_base} | {assigned_user.username} | R{routine_index:02d}"

            if task_template_exists(
                db=db,
                business_id=business.id,
                assigned_to_user_id=assigned_user.id,
                title=title,
            ):
                continue

            due_hour = 8 + ((routine_index + user_index) % 10)
            due_minute = (routine_index * 10) % 60

            create_routine_task_template(
                db=db,
                current_user=owner,
                business=business,
                assigned_to_user=assigned_user,
                title=title,
                description=(
                    f"Load test rutin görevi. İşletme={business_no}, "
                    f"kullanıcı={assigned_user.username}, sıra={routine_index}."
                ),
                default_due_time_local=time(hour=due_hour, minute=due_minute),
                requires_photo=(routine_index % 3 == 0),
                requires_location=(routine_index % 4 == 0),
                requires_manager_approval=(routine_index % 2 == 0),
            )
            created_template_count += 1

        for extra_index in range(1, extra_per_user + 1):
            title_base = EXTRA_TASK_TITLES[(extra_index - 1) % len(EXTRA_TASK_TITLES)]
            title = f"{title_base} | {assigned_user.username} | E{extra_index:02d}"

            if extra_task_exists(
                db=db,
                business_id=business.id,
                assigned_to_user_id=assigned_user.id,
                title=title,
            ):
                continue

            due_at = get_utc_now() + timedelta(hours=(extra_index % 8) + 1)

            create_extra_task(
                db=db,
                current_user=owner,
                business=business,
                assigned_to_user=assigned_user,
                title=title,
                description=(
                    f"Load test tek seferlik görev. İşletme={business_no}, "
                    f"kullanıcı={assigned_user.username}, sıra={extra_index}."
                ),
                priority="high" if extra_index % 5 == 0 else "normal",
                due_at_utc=due_at,
                requires_photo=(extra_index % 3 == 0),
                requires_location=(extra_index % 4 == 0),
                requires_manager_approval=(extra_index % 2 == 0),
                ip_address="127.0.0.1",
                user_agent="Missio local multitenant load seed",
            )
            created_extra_task_count += 1

    generation_result = generate_daily_routine_tasks(
        db=db,
        current_user=owner,
        business=business,
        task_date=None,
        assigned_to_user_id=None,
        ip_address="127.0.0.1",
        user_agent="Missio local multitenant load seed",
    )

    db.flush()

    return {
        "businesses": 1,
        "users": created_user_count,
        "assignable_users": len(assignable_users),
        "routine_templates": created_template_count,
        "routine_tasks": generation_result.created_count,
        "extra_tasks": created_extra_task_count,
        "routine_skipped": generation_result.skipped_count,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Missio lokal ortamında çok kiracılı yük testi için yoğun test verisi üretir. "
            "Canlı veritabanında kullanmayın."
        )
    )
    parser.add_argument("--business-count", type=int, default=DEFAULT_BUSINESS_COUNT)
    parser.add_argument("--manager-count", type=int, default=DEFAULT_MANAGER_COUNT)
    parser.add_argument("--staff-count", type=int, default=DEFAULT_STAFF_COUNT)
    parser.add_argument("--routine-per-user", type=int, default=DEFAULT_ROUTINE_PER_USER)
    parser.add_argument("--extra-per-user", type=int, default=DEFAULT_EXTRA_PER_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d%H%M%S"))
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.yes:
        raise RuntimeError("Çalıştırmak için --yes parametresi zorunludur.")

    if args.business_count < 1 or args.business_count > 50:
        raise RuntimeError("--business-count 1 ile 50 arasında olmalıdır.")

    if args.manager_count < 1 or args.manager_count > 20:
        raise RuntimeError("--manager-count 1 ile 20 arasında olmalıdır.")

    if args.staff_count < 1 or args.staff_count > 200:
        raise RuntimeError("--staff-count 1 ile 200 arasında olmalıdır.")

    total_business_users = 1 + args.manager_count + args.staff_count

    if total_business_users > 50:
        raise RuntimeError(
            "Bu komut varsayılan trial planını local load test için 50 kullanıcıya yükseltir. "
            "İşletme başına kullanıcı sayısı 50'yi geçmemelidir."
        )

    if args.routine_per_user < 1 or args.routine_per_user > 20:
        raise RuntimeError("--routine-per-user 1 ile 20 arasında olmalıdır.")

    if args.extra_per_user < 1 or args.extra_per_user > 20:
        raise RuntimeError("--extra-per-user 1 ile 20 arasında olmalıdır.")


def main() -> None:
    args = build_parser().parse_args()
    validate_args(args)
    ensure_seed_is_allowed(force=args.force)

    db = SessionLocal()

    totals = {
        "businesses": 0,
        "users": 0,
        "assignable_users": 0,
        "routine_templates": 0,
        "routine_tasks": 0,
        "extra_tasks": 0,
        "routine_skipped": 0,
    }

    try:
        print("[INFO] Missio local multitenant load seed başlıyor.")
        print(f"[INFO] ENVIRONMENT: {settings.environment}")
        print(f"[INFO] DATABASE_URL: {settings.database_url}")
        print(f"[INFO] RUN_ID: {args.run_id}")
        print(
            "[INFO] Hedef: "
            f"{args.business_count} işletme, "
            f"işletme başına {1 + args.manager_count + args.staff_count} kullanıcı "
            f"(1 patron + {args.manager_count} yönetici + {args.staff_count} personel), "
            f"atanabilir kullanıcı başına {args.routine_per_user} rutin + "
            f"{args.extra_per_user} tek seferlik görev."
        )

        super_admin = get_active_super_admin(db)
        ensure_trial_plan(db)
        db.commit()

        for business_index in range(1, args.business_count + 1):
            stats = create_business_block(
                db=db,
                super_admin=super_admin,
                run_id=args.run_id,
                business_index=business_index,
                manager_count=args.manager_count,
                staff_count=args.staff_count,
                routine_per_user=args.routine_per_user,
                extra_per_user=args.extra_per_user,
                password=args.password,
            )

            db.commit()

            for key, value in stats.items():
                totals[key] += value

            print(
                f"[OK] İşletme {business_index:03d}/{args.business_count:03d} hazırlandı | "
                f"users={stats['users']} | "
                f"routine_templates={stats['routine_templates']} | "
                f"routine_tasks={stats['routine_tasks']} | "
                f"extra_tasks={stats['extra_tasks']}"
            )

        print("")
        print("[OK] Load test verisi tamamlandı.")
        print(f"[OK] İşletme: {totals['businesses']}")
        print(f"[OK] Kullanıcı: {totals['users']} + mevcut super_admin")
        print(f"[OK] Görev atanabilir kullanıcı: {totals['assignable_users']}")
        print(f"[OK] Rutin şablon: {totals['routine_templates']}")
        print(f"[OK] Bugünkü rutin görev: {totals['routine_tasks']}")
        print(f"[OK] Tek seferlik görev: {totals['extra_tasks']}")
        print(f"[OK] Rutin skipped: {totals['routine_skipped']}")
        print("")
        print("[INFO] Örnek girişler:")
        print(f"  business 001 patron: username=boss001 password={args.password}")
        print(f"  business 001 manager: username=manager00101 password={args.password}")
        print(f"  business 001 staff: username=staff00101 password={args.password}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
