from __future__ import annotations

import sys

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.services.bootstrap_service import get_bootstrap_status


def main() -> None:
    """Check initial bootstrap status."""

    db = SessionLocal()

    try:
        status = get_bootstrap_status(db)
        db.commit()

        print("Missio bootstrap durum kontrolü")
        print(f"user_count: {status.user_count}")
        print(f"super_admin_count: {status.super_admin_count}")
        print(f"setup_completed: {status.setup_completed}")
        print(f"is_ready_for_initial_setup: {status.is_ready_for_initial_setup}")
        print(f"is_completed: {status.is_completed}")
        print(f"is_consistent: {status.is_consistent}")
        print(f"message: {status.message}")

        if not status.is_consistent:
            print("Bootstrap durum kontrolü başarısız.")
            sys.exit(1)

        print("Bootstrap durum kontrolü başarılı.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
