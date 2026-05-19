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
