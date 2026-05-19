from fastapi import APIRouter, Depends

from app.api.dependencies import require_roles_dependency
from app.db.session import check_database_connection, get_sqlite_runtime_settings
from app.models.user import User

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/health")
def database_health_check(
    current_user: User = Depends(require_roles_dependency("super_admin")),
) -> dict[str, object]:
    """Return database connection and SQLite runtime health details."""

    del current_user

    return {
        "connection": check_database_connection(),
        "runtime": get_sqlite_runtime_settings(),
    }
