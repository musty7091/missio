from fastapi import APIRouter

from app.api.routes import auth, business_users, db_health, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(db_health.router)
api_router.include_router(auth.router)
api_router.include_router(business_users.router)
