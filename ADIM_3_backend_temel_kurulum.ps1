# Missio - ADIM 3
# Backend temel FastAPI kurulum dosyalarını oluşturur.
# Bu dosyayı C:\missio içinde çalıştır.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "C:\missio"

New-Item -ItemType Directory -Force -Path "backend" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\api" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\api\routes" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\core" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\db" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\models" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\schemas" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\services" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\repositories" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\modules" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\utils" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\tests" | Out-Null

@'
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.5
pydantic-settings==2.7.1
python-dotenv==1.0.1
SQLAlchemy==2.0.37
alembic==1.14.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.20
pytest==8.3.4
httpx==0.28.1
'@ | Set-Content -Encoding UTF8 "backend\requirements.txt"

@'
MISSIO_APP_NAME=Missio
MISSIO_ENVIRONMENT=local
MISSIO_DEBUG=true
MISSIO_DEFAULT_TIMEZONE=Europe/Istanbul
MISSIO_DATABASE_URL=sqlite:///./missio_local.db
MISSIO_SECRET_KEY=change-this-secret-key-before-production
MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES=60
'@ | Set-Content -Encoding UTF8 "backend\.env.example"

@'
"""Missio backend application package."""
'@ | Set-Content -Encoding UTF8 "backend\app\__init__.py"

@'
"""API package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\api\__init__.py"

@'
"""Route package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\api\routes\__init__.py"

@'
"""Core package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\core\__init__.py"

@'
"""Database package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\db\__init__.py"

@'
"""Model package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\models\__init__.py"

@'
"""Schema package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\schemas\__init__.py"

@'
"""Service package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\services\__init__.py"

@'
"""Repository package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\repositories\__init__.py"

@'
"""Module package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\modules\__init__.py"

@'
"""Utility package for Missio backend."""
'@ | Set-Content -Encoding UTF8 "backend\app\utils\__init__.py"

@'
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="Missio", alias="MISSIO_APP_NAME")
    environment: str = Field(default="local", alias="MISSIO_ENVIRONMENT")
    debug: bool = Field(default=True, alias="MISSIO_DEBUG")
    default_timezone: str = Field(default="Europe/Istanbul", alias="MISSIO_DEFAULT_TIMEZONE")
    database_url: str = Field(default="sqlite:///./missio_local.db", alias="MISSIO_DATABASE_URL")
    secret_key: str = Field(
        default="change-this-secret-key-before-production",
        alias="MISSIO_SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        alias="MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()
'@ | Set-Content -Encoding UTF8 "backend\app\core\config.py"

@'
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
'@ | Set-Content -Encoding UTF8 "backend\app\api\routes\health.py"

@'
from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
'@ | Set-Content -Encoding UTF8 "backend\app\api\router.py"

@'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        description="Missio - Mission is possible.",
    )

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
'@ | Set-Content -Encoding UTF8 "backend\app\main.py"

@'
# Missio Backend

FastAPI backend for Missio.

## Local development

```powershell
cd C:\missio\backend
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/api/v1/health
```
'@ | Set-Content -Encoding UTF8 "backend\README.md"

Write-Host ""
Write-Host "ADIM 3 dosyalari olusturuldu." -ForegroundColor Green
Write-Host "Simdi su komutlari calistir:" -ForegroundColor Cyan
Write-Host ""
Write-Host "cd C:\missio\backend"
Write-Host "python -m venv .venv"
Write-Host ".\.venv\Scripts\activate"
Write-Host "python -m pip install --upgrade pip"
Write-Host "pip install -r requirements.txt"
Write-Host "copy .env.example .env"
Write-Host "uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host ""
