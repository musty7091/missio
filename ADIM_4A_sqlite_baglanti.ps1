# Missio - ADIM 4A
# SQLite baglanti temeli ve veritabani saglik kontrol endpointini olusturur.
# Bu dosyayi C:\missio icinde calistir.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "C:\missio"

New-Item -ItemType Directory -Force -Path "backend\app\db" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\api\routes" | Out-Null

@'
from sqlalchemy import event
from sqlalchemy.engine import Engine


def configure_sqlite_connection(dbapi_connection, connection_record) -> None:
    """Apply safe SQLite pragmas for each new database connection."""

    del connection_record

    cursor = dbapi_connection.cursor()

    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")

    cursor.close()


def register_sqlite_pragmas(engine: Engine) -> None:
    """Register SQLite pragma configuration on the given SQLAlchemy engine."""

    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    event.listen(engine, "connect", configure_sqlite_connection)
'@ | Set-Content -Encoding UTF8 "backend\app\db\sqlite.py"

@'
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.sqlite import register_sqlite_pragmas

connect_args: dict[str, bool] = {}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

register_sqlite_pragmas(engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for FastAPI dependencies."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> dict[str, str]:
    """Run a minimal database connection check."""

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    return {
        "status": "ok",
        "database": engine.url.get_backend_name(),
        "result": str(result),
    }


def get_sqlite_runtime_settings() -> dict[str, str]:
    """Return important SQLite runtime settings for diagnostics."""

    if not settings.database_url.startswith("sqlite"):
        return {
            "database": engine.url.get_backend_name(),
            "message": "SQLite runtime settings are not applicable.",
        }

    with engine.connect() as connection:
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
        journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()
        synchronous = connection.execute(text("PRAGMA synchronous")).scalar_one()
        busy_timeout = connection.execute(text("PRAGMA busy_timeout")).scalar_one()

    return {
        "database": "sqlite",
        "foreign_keys": str(foreign_keys),
        "journal_mode": str(journal_mode),
        "synchronous": str(synchronous),
        "busy_timeout": str(busy_timeout),
    }
'@ | Set-Content -Encoding UTF8 "backend\app\db\session.py"

@'
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
'@ | Set-Content -Encoding UTF8 "backend\app\db\base.py"

@'
from fastapi import APIRouter

from app.db.session import check_database_connection, get_sqlite_runtime_settings

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/health")
def database_health_check() -> dict[str, object]:
    """Return database connection and SQLite runtime health details."""

    return {
        "connection": check_database_connection(),
        "runtime": get_sqlite_runtime_settings(),
    }
'@ | Set-Content -Encoding UTF8 "backend\app\api\routes\db_health.py"

@'
from fastapi import APIRouter

from app.api.routes import db_health, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(db_health.router)
'@ | Set-Content -Encoding UTF8 "backend\app\api\router.py"

Write-Host ""
Write-Host "ADIM 4A dosyalari olusturuldu." -ForegroundColor Green
Write-Host "Test icin backend klasorunde sunucuyu tekrar baslat:" -ForegroundColor Cyan
Write-Host ""
Write-Host "cd C:\missio\backend"
Write-Host ".\.venv\Scripts\activate"
Write-Host "uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host ""
Write-Host "Sonra tarayicida ac:"
Write-Host "http://127.0.0.1:8000/api/v1/db/health"
Write-Host ""
