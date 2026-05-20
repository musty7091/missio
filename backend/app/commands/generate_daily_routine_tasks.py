from __future__ import annotations

import argparse
from datetime import date, datetime

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.roles import UserRole
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.user import User
from app.services.task_service import generate_daily_routine_tasks


def parse_task_date(value: str | None) -> date | None:
    """Parse task date from YYYY-MM-DD text."""

    if value is None:
        return None

    return datetime.strptime(value, "%Y-%m-%d").date()


def get_system_actor(db) -> User:
    """Return an active super admin user for maintenance command operations."""

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
            "Aktif super_admin kullanıcı bulunamadı. "
            "Günlük rutin görev üretimi için en az bir aktif super_admin gerekli."
        )

    return user


def get_target_businesses(
    db,
    *,
    business_id: int | None,
) -> list[Business]:
    """Return active businesses for routine task generation."""

    query = select(Business).where(Business.is_active.is_(True))

    if business_id is not None:
        query = query.where(Business.id == business_id)

    businesses = db.execute(query.order_by(Business.id.asc())).scalars().all()

    if business_id is not None and not businesses:
        raise RuntimeError(f"İşletme bulunamadı veya aktif değil. business_id={business_id}")

    return list(businesses)


def main() -> None:
    """Generate daily routine tasks for one or all active businesses."""

    parser = argparse.ArgumentParser(
        description="Missio günlük rutin görev üretim komutu."
    )
    parser.add_argument(
        "--business-id",
        type=int,
        default=None,
        help="Sadece belirli bir işletme için rutin görev üretir.",
    )
    parser.add_argument(
        "--assigned-to-user-id",
        type=int,
        default=None,
        help="Sadece belirli bir kullanıcı için rutin görev üretir.",
    )
    parser.add_argument(
        "--task-date",
        type=str,
        default=None,
        help="Görev tarihi. Format: YYYY-MM-DD. Boş bırakılırsa işletmenin bugünü kullanılır.",
    )

    args = parser.parse_args()
    selected_task_date = parse_task_date(args.task_date)

    db = SessionLocal()

    try:
        system_actor = get_system_actor(db)
        businesses = get_target_businesses(
            db=db,
            business_id=args.business_id,
        )

        total_created_count = 0
        total_skipped_count = 0

        print("[INFO] Günlük rutin görev üretimi başladı.")
        print(f"[INFO] İşlem kullanıcısı: {system_actor.username} ({system_actor.role})")

        if selected_task_date is not None:
            print(f"[INFO] Seçili görev tarihi: {selected_task_date}")

        if args.assigned_to_user_id is not None:
            print(f"[INFO] Kullanıcı filtresi: {args.assigned_to_user_id}")

        for business in businesses:
            result = generate_daily_routine_tasks(
                db=db,
                current_user=system_actor,
                business=business,
                task_date=selected_task_date,
                assigned_to_user_id=args.assigned_to_user_id,
                ip_address="127.0.0.1",
                user_agent="Missio command generate_daily_routine_tasks",
            )

            total_created_count += result.created_count
            total_skipped_count += result.skipped_count

            print(
                "[OK] "
                f"business_id={business.id} | "
                f"name={business.name} | "
                f"task_date={result.task_date} | "
                f"created={result.created_count} | "
                f"skipped={result.skipped_count}"
            )

        db.commit()

        print("[OK] Günlük rutin görev üretimi tamamlandı.")
        print(f"[OK] Toplam oluşturulan görev: {total_created_count}")
        print(f"[OK] Toplam atlanan kayıt: {total_skipped_count}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()