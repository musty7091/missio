from __future__ import annotations

from sqlalchemy import select

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.task import Task
from app.models.user import User
from app.repositories.user_repository import normalize_username
from app.services.task_service import (
    get_business_today,
    get_my_today_tasks,
    list_incomplete_tasks_for_report,
)


BUSINESS_SLUG = "missio-demo-market"

OWNER_USERNAME = "patron"
MANAGER_USERNAME = "manager"
STAFF_USERNAME = "ahmet"
SECOND_STAFF_USERNAME = "ali"


def get_demo_business(db) -> Business:
    """Return demo business."""

    business = (
        db.execute(select(Business).where(Business.slug == BUSINESS_SLUG))
        .scalars()
        .first()
    )

    if business is None:
        raise RuntimeError(
            "Demo işletme bulunamadı. Önce şu komutu çalıştırın: "
            "python -m app.commands.dev.seed_local_task_demo_data"
        )

    return business


def get_demo_user(
    db,
    *,
    business_id: int,
    username: str,
) -> User:
    """Return demo business user."""

    user = (
        db.execute(
            select(User).where(
                User.business_id == business_id,
                User.username == normalize_username(username),
            )
        )
        .scalars()
        .first()
    )

    if user is None:
        raise RuntimeError(
            f"Demo kullanıcı bulunamadı: {username}. "
            "Önce şu komutu çalıştırın: "
            "python -m app.commands.dev.seed_local_task_demo_data"
        )

    return user


def print_task_list(title: str, tasks: list[Task]) -> None:
    """Print task list."""

    print("")
    print(title)
    print("-" * len(title))

    if not tasks:
        print("(kayıt yok)")
        return

    for task in tasks:
        print(
            f"id={task.id} | "
            f"type={task.task_type} | "
            f"status={task.status} | "
            f"assigned_to_user_id={task.assigned_to_user_id} | "
            f"title={task.title}"
        )


def assert_minimum_count(
    *,
    label: str,
    actual_count: int,
    minimum_count: int,
) -> None:
    """Raise if actual count is below expected minimum."""

    if actual_count < minimum_count:
        raise RuntimeError(
            f"{label} beklenen minimum sayının altında. "
            f"Beklenen en az: {minimum_count}, Gelen: {actual_count}"
        )


def main() -> None:
    """Check local task demo flow."""

    db = SessionLocal()

    try:
        business = get_demo_business(db)
        owner = get_demo_user(
            db=db,
            business_id=business.id,
            username=OWNER_USERNAME,
        )
        manager = get_demo_user(
            db=db,
            business_id=business.id,
            username=MANAGER_USERNAME,
        )
        staff = get_demo_user(
            db=db,
            business_id=business.id,
            username=STAFF_USERNAME,
        )
        second_staff = get_demo_user(
            db=db,
            business_id=business.id,
            username=SECOND_STAFF_USERNAME,
        )

        task_date = get_business_today(business)

        print("[INFO] Missio görev demo akışı kontrolü başladı.")
        print(f"[INFO] İşletme: {business.name} | business_id={business.id}")
        print(f"[INFO] Görev tarihi: {task_date}")
        print(f"[INFO] Owner: {owner.username} ({owner.role})")
        print(f"[INFO] Manager: {manager.username} ({manager.role})")
        print(f"[INFO] Staff 1: {staff.username} ({staff.role})")
        print(f"[INFO] Staff 2: {second_staff.username} ({second_staff.role})")

        staff_today = get_my_today_tasks(
            db=db,
            current_user=staff,
            business=business,
            task_date=task_date,
            ip_address="127.0.0.1",
            user_agent="Missio command check_task_demo_flow",
        )

        second_staff_today = get_my_today_tasks(
            db=db,
            current_user=second_staff,
            business=business,
            task_date=task_date,
            ip_address="127.0.0.1",
            user_agent="Missio command check_task_demo_flow",
        )

        manager_today = get_my_today_tasks(
            db=db,
            current_user=manager,
            business=business,
            task_date=task_date,
            ip_address="127.0.0.1",
            user_agent="Missio command check_task_demo_flow",
        )

        db.commit()

        print_task_list(
            "Ahmet - Bugünkü Rutin Görevler",
            staff_today.routine_tasks,
        )
        print_task_list(
            "Ahmet - Bugünkü Ekstra Görevler",
            staff_today.extra_tasks,
        )
        print_task_list(
            "Ali - Bugünkü Rutin Görevler",
            second_staff_today.routine_tasks,
        )
        print_task_list(
            "Ali - Bugünkü Ekstra Görevler",
            second_staff_today.extra_tasks,
        )
        print_task_list(
            "Manager - Bugünkü Rutin Görevler",
            manager_today.routine_tasks,
        )
        print_task_list(
            "Manager - Bugünkü Ekstra Görevler",
            manager_today.extra_tasks,
        )

        assert_minimum_count(
            label="Ahmet rutin görevleri",
            actual_count=len(staff_today.routine_tasks),
            minimum_count=3,
        )
        assert_minimum_count(
            label="Ahmet ekstra görevleri",
            actual_count=len(staff_today.extra_tasks),
            minimum_count=1,
        )
        assert_minimum_count(
            label="Ali rutin görevleri",
            actual_count=len(second_staff_today.routine_tasks),
            minimum_count=1,
        )
        assert_minimum_count(
            label="Ali ekstra görevleri",
            actual_count=len(second_staff_today.extra_tasks),
            minimum_count=1,
        )
        assert_minimum_count(
            label="Manager rutin görevleri",
            actual_count=len(manager_today.routine_tasks),
            minimum_count=1,
        )

        incomplete_report = list_incomplete_tasks_for_report(
            db=db,
            current_user=owner,
            business=business,
            task_date=task_date,
            assigned_to_user_id=None,
            limit=500,
            offset=0,
        )

        print_task_list(
            "Gün Sonu Tamamlanmayan Görevler",
            incomplete_report.tasks,
        )

        assert_minimum_count(
            label="Gün sonu tamamlanmayan görevler",
            actual_count=incomplete_report.total_count,
            minimum_count=1,
        )

        print("")
        print("[OK] Ahmet günlük görev ekranı kontrolü başarılı.")
        print("[OK] Ali günlük görev ekranı kontrolü başarılı.")
        print("[OK] Manager günlük görev ekranı kontrolü başarılı.")
        print("[OK] Gün sonu tamamlanmayan görev raporu kontrolü başarılı.")
        print("[OK] Missio görev demo akışı başarılı.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()