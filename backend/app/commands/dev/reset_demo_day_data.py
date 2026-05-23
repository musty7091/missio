from __future__ import annotations

import os

from sqlalchemy import delete, select

import app.models  # noqa: F401
from app.commands.dev.seed_local_task_demo_data import (
    BUSINESS_SLUG,
    main as seed_demo_data,
)
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.daily_operation_closure import DailyOperationClosure
from app.models.daily_operation_closure_item import DailyOperationClosureItem
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.models.task_event import TaskEvent
from app.services.task_service import get_business_today


def main() -> None:
    db = SessionLocal()

    try:
        business = (
            db.execute(
                select(Business).where(Business.slug == BUSINESS_SLUG)
            )
            .scalars()
            .first()
        )

        if business is None:
            print("[INFO] Demo işletme bulunamadı. Sadece seed çalıştırılacak.")
            db.close()
            os.environ["MISSIO_ALLOW_DEMO_SEED"] = "1"
            seed_demo_data()
            return

        task_date = get_business_today(business)

        task_ids = list(
            db.execute(
                select(Task.id).where(
                    Task.business_id == business.id,
                    Task.task_date == task_date,
                    Task.deleted_at_utc.is_(None),
                )
            )
            .scalars()
            .all()
        )

        deleted_attachment_count = 0
        deleted_event_count = 0
        deleted_closure_item_count = 0
        deleted_closure_count = 0
        deleted_task_count = 0

        if task_ids:
            deleted_attachment_count = (
                db.execute(
                    delete(TaskAttachment).where(
                        TaskAttachment.business_id == business.id,
                        TaskAttachment.task_id.in_(task_ids),
                    )
                ).rowcount
                or 0
            )

            deleted_event_count = (
                db.execute(
                    delete(TaskEvent).where(
                        TaskEvent.business_id == business.id,
                        TaskEvent.task_id.in_(task_ids),
                    )
                ).rowcount
                or 0
            )

        deleted_closure_item_count = (
            db.execute(
                delete(DailyOperationClosureItem).where(
                    DailyOperationClosureItem.business_id == business.id,
                    DailyOperationClosureItem.task_date == task_date,
                )
            ).rowcount
            or 0
        )

        deleted_closure_count = (
            db.execute(
                delete(DailyOperationClosure).where(
                    DailyOperationClosure.business_id == business.id,
                    DailyOperationClosure.closure_date == task_date,
                )
            ).rowcount
            or 0
        )

        if task_ids:
            deleted_task_count = (
                db.execute(
                    delete(Task).where(
                        Task.business_id == business.id,
                        Task.id.in_(task_ids),
                    )
                ).rowcount
                or 0
            )

        db.commit()

        print("[OK] Bugünün demo verisi temizlendi.")
        print(f"[OK] İşletme: {business.name} | business_id={business.id}")
        print(f"[OK] Tarih: {task_date}")
        print(f"[OK] Silinen ek dosya kaydı: {deleted_attachment_count}")
        print(f"[OK] Silinen görev olay kaydı: {deleted_event_count}")
        print(f"[OK] Silinen kapanış detay kaydı: {deleted_closure_item_count}")
        print(f"[OK] Silinen kapanış kaydı: {deleted_closure_count}")
        print(f"[OK] Silinen görev kaydı: {deleted_task_count}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    os.environ["MISSIO_ALLOW_DEMO_SEED"] = "1"
    seed_demo_data()


if __name__ == "__main__":
    main()
