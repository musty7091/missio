from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base


BASELINE_REVISION = "7f15391ac7c5"


def resolve_sqlite_database_path() -> Path:
    """Resolve sqlite database path from application settings."""

    url = make_url(settings.database_url)

    if url.drivername != "sqlite":
        raise RuntimeError(
            "Bu komut sadece local SQLite veritabanı için kullanılabilir. "
            f"Mevcut DATABASE_URL: {settings.database_url}"
        )

    if not url.database or url.database == ":memory:":
        raise RuntimeError("Geçerli bir SQLite dosya yolu bulunamadı.")

    database_path = Path(url.database)

    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path

    return database_path.resolve()


def backup_database_files(database_path: Path) -> Path:
    """Backup sqlite database files if they exist."""

    backup_dir = database_path.parent / "_db_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{database_path.stem}_{timestamp}{database_path.suffix}"

    if database_path.exists():
        shutil.copy2(database_path, backup_file)
        print(f"[OK] Veritabanı yedeği alındı: {backup_file}")
    else:
        print("[INFO] Yedeklenecek ana veritabanı dosyası bulunamadı.")

    for suffix in ("-wal", "-shm"):
        side_file = Path(f"{database_path}{suffix}")

        if side_file.exists():
            side_backup_file = backup_dir / f"{database_path.name}{suffix}_{timestamp}"
            shutil.copy2(side_file, side_backup_file)
            print(f"[OK] SQLite yan dosya yedeği alındı: {side_backup_file}")

    return backup_file


def delete_database_files(database_path: Path) -> None:
    """Delete sqlite database files."""

    files_to_delete = [
        database_path,
        Path(f"{database_path}-wal"),
        Path(f"{database_path}-shm"),
    ]

    for file_path in files_to_delete:
        if file_path.exists():
            file_path.unlink()
            print(f"[OK] Silindi: {file_path}")


def create_fresh_database(database_path: Path) -> None:
    """Create fresh database from current SQLAlchemy models."""

    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS alembic_version "
                "(version_num VARCHAR(32) NOT NULL)"
            )
        )
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text(
                "INSERT INTO alembic_version (version_num) "
                "VALUES (:version_num)"
            ),
            {"version_num": BASELINE_REVISION},
        )

    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())

    required_tables = {
        "app_settings",
        "businesses",
        "users",
        "tasks",
        "task_templates",
        "task_categories",
        "task_events",
        "task_attachments",
        "alembic_version",
    }

    missing_tables = sorted(required_tables - set(tables))

    if missing_tables:
        raise RuntimeError(f"Eksik tablolar var: {missing_tables}")

    with engine.connect() as connection:
        revision_rows = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).fetchall()

    if revision_rows != [(BASELINE_REVISION,)]:
        raise RuntimeError(
            "Alembic revision kaydı beklenen değerde değil. "
            f"Gelen kayıtlar: {revision_rows}"
        )

    print("[OK] Temiz SQLite veritabanı oluşturuldu.")
    print(f"[OK] Alembic revision yazıldı: {BASELINE_REVISION}")


def main() -> None:
    """Reset local sqlite database after explicit confirmation."""

    parser = argparse.ArgumentParser(
        description="Missio local SQLite veritabanını sıfırlar."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Onay sorusunu geçerek sıfırlama işlemini başlatır.",
    )
    args = parser.parse_args()

    if not args.yes:
        raise RuntimeError(
            "Bu komut veritabanını sıfırlar. Çalıştırmak için --yes ekleyin."
        )

    database_path = resolve_sqlite_database_path()

    print(f"[INFO] DATABASE_URL: {settings.database_url}")
    print(f"[INFO] SQLite dosyası: {database_path}")

    backup_database_files(database_path)
    delete_database_files(database_path)
    create_fresh_database(database_path)

    print("[OK] Local geliştirme veritabanı sıfırlama tamamlandı.")


if __name__ == "__main__":
    main()