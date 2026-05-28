from fastapi import APIRouter

from app.api.routes import (
    auth,
    businesses,
    business_users,
    daily_closures,
    db_health,
    health,
    location_checks,
    password_reset_requests,
    push_notifications,
    tasks,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(db_health.router)
api_router.include_router(auth.router)
api_router.include_router(push_notifications.router)
api_router.include_router(businesses.router)
api_router.include_router(business_users.router)
api_router.include_router(daily_closures.router)
api_router.include_router(location_checks.router)
api_router.include_router(password_reset_requests.router)
api_router.include_router(tasks.router)
