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
