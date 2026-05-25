from __future__ import annotations

import argparse
import importlib
import pkgutil
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import app.models
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.subscription_plan import SubscriptionPlan
from app.services.bootstrap_service import create_initial_super_admin


def import_all_models() -> None:
    """Import every model module so Base.metadata contains all tables."""

    for module_info in pkgutil.iter_modules(app.models.__path__):
        if not module_info.ispkg:
            importlib.import_module(f"app.models.{module_info.name}")


def resolve_sqlite_database_path() -> Path:
    """Resolve SQLite database path from current app settings."""

    url = make_url(settings.database_url)

    if url.drivername != "sqlite":
        raise RuntimeError(
            "Bu komut sadece local/test SQLite veritabanı için kullanılabilir. "
            f"Mevcut DATABASE_URL: {settings.database_url}"
        )

    if not url.database or url.database == ":memory:":
        raise RuntimeError("Geçerli bir SQLite dosya yolu bulunamadı.")

    database_path = Path(url.database)

    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path

    return database_path.resolve()


def delete_sqlite_database_files(database_path: Path) -> None:
    """Delete SQLite database file and WAL/SHM side files."""

    targets = [
        database_path,
        Path(f"{database_path}-wal"),
        Path(f"{database_path}-shm"),
    ]

    for target in targets:
        if target.exists():
            target.unlink()
            print(f"[OK] Silindi: {target}")


def create_alembic_version_marker(db: Session, version_num: str) -> None:
    """
    Mark local clean database as current schema.

    Bu komut migration çalıştırmaz. Boş local DB zaten güncel modellerden
    oluşturulduğu için sadece alembic_version işaretini güncel tutar.
    """

    db.execute(
        text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL)"
        )
    )
    db.execute(text("DELETE FROM alembic_version"))
    db.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"),
        {"version_num": version_num},
    )


def seed_subscription_plans(db: Session) -> None:
    """Seed required subscription plans for first business creation."""

    now = datetime.now(timezone.utc)

    plans = [
        {
            "code": "trial",
            "name": "Deneme",
            "description": "Test ve deneme kullanımı için ücretsiz plan.",
            "max_users": 20,
            "max_managers": 5,
            "max_daily_tasks": 500,
            "report_retention_days": 60,
            "price_monthly": None,
            "price_yearly": None,
            "currency": "TRY",
            "display_order": 1,
        },
        {
            "code": "starter",
            "name": "Başlangıç",
            "description": "Küçük ekipler için başlangıç planı.",
            "max_users": 10,
            "max_managers": 2,
            "max_daily_tasks": 250,
            "report_retention_days": 60,
            "price_monthly": Decimal("499.00"),
            "price_yearly": Decimal("4990.00"),
            "currency": "TRY",
            "display_order": 10,
        },
        {
            "code": "business",
            "name": "Business",
            "description": "Büyüyen işletmeler için standart plan.",
            "max_users": 30,
            "max_managers": 8,
            "max_daily_tasks": 1000,
            "report_retention_days": 180,
            "price_monthly": Decimal("999.00"),
            "price_yearly": Decimal("9990.00"),
            "currency": "TRY",
            "display_order": 20,
        },
        {
            "code": "pro",
            "name": "Pro",
            "description": "Yoğun operasyon kullanan işletmeler için profesyonel plan.",
            "max_users": 75,
            "max_managers": 20,
            "max_daily_tasks": 3000,
            "report_retention_days": 365,
            "price_monthly": Decimal("1999.00"),
            "price_yearly": Decimal("19990.00"),
            "currency": "TRY",
            "display_order": 30,
        },
        {
            "code": "enterprise",
            "name": "Enterprise",
            "description": "Özel kurumsal kullanım planı.",
            "max_users": 250,
            "max_managers": 100,
            "max_daily_tasks": 10000,
            "report_retention_days": 1095,
            "price_monthly": None,
            "price_yearly": None,
            "currency": "TRY",
            "display_order": 40,
        },
    ]

    for plan_data in plans:
        exists = (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.code == plan_data["code"])
            .one_or_none()
        )

        if exists is not None:
            continue

        db.add(
            SubscriptionPlan(
                **plan_data,
                is_active=True,
                created_at_utc=now,
                updated_at_utc=now,
            )
        )

    db.flush()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Missio local/test SQLite veritabanını sıfırdan eksiksiz kurar.",
    )
    parser.add_argument("--reset", action="store_true", help="Mevcut SQLite DB dosyasını siler.")
    parser.add_argument("--yes", action="store_true", help="Onay sorusunu geçer.")
    parser.add_argument("--admin-full-name", default="Mustafa Karadeniz")
    parser.add_argument("--admin-username", default="admin")
    parser.add_argument("--admin-email", default="m.mkaradeniz@icloud.com")
    parser.add_argument("--admin-password", required=True)
    parser.add_argument(
        "--schema-version",
        default="webpush2026052501",
        help="Temiz kurulan DB için alembic_version değeri.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.reset and not args.yes:
        raise RuntimeError("DB sıfırlamak için --yes parametresi de verilmelidir.")

    import_all_models()

    database_path = resolve_sqlite_database_path()

    print(f"[INFO] DATABASE_URL: {settings.database_url}")
    print(f"[INFO] SQLite DB: {database_path}")

    if args.reset:
        delete_sqlite_database_files(database_path)

    if database_path.exists() and not args.reset:
        raise RuntimeError(
            "Veritabanı dosyası zaten var. Temiz kurulum için --reset --yes kullanın."
        )

    database_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        create_alembic_version_marker(db=db, version_num=args.schema_version)
        seed_subscription_plans(db=db)

        admin_user = create_initial_super_admin(
            db=db,
            full_name=args.admin_full_name,
            username=args.admin_username,
            password=args.admin_password,
            email=args.admin_email,
            ip_address="local-init",
            user_agent="Missio local init command",
        )

        db.commit()
        db.refresh(admin_user)

        print("")
        print("[OK] Temiz local/test veritabanı eksiksiz oluşturuldu.")
        print("[OK] Tüm tablolar güncel modellerden oluşturuldu.")
        print("[OK] Abonelik planları eklendi.")
        print("[OK] İlk super_admin oluşturuldu.")
        print(f"[OK] Schema version: {args.schema_version}")
        print("")
        print(f"Kullanıcı adı: {admin_user.username}")
        print("Şifre: komutta verilen şifre")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
