from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    """Return a basic health response for the backend."""

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "timezone": settings.default_timezone,
    }
