from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.http_security import add_security_headers
from app.core.rate_limit import add_rate_limit
from app.core.security_config import is_production_environment


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    is_production = is_production_environment(settings.environment)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        description="Missio - Mission is possible.",
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    app.middleware("http")(add_security_headers)
    app.middleware("http")(add_rate_limit)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "message": "Missio backend is running.",
            "slogan": "Mission is possible.",
        }

    return app


app = create_app()
