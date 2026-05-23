# Missio Cloud Config Inventory

Generated at: 2026-05-23 11:22:19

Bu dosya cloud geçişi öncesi yapılandırma envanteridir.
Gizli değerler rapora yazılmaz; hassas env değerleri maskelenir.

## Dosya Durumu

- `backend/app/core/config.py`: **VAR**
- `backend/app/main.py`: **VAR**
- `backend/app/db/session.py`: **VAR**
- `backend/app/db/base.py`: **VAR**
- `backend/requirements.txt`: **VAR**
- `backend/.env`: **VAR**
- `backend/.env.example`: **VAR**
- `frontend/src/config/api.ts`: **VAR**
- `frontend/package.json`: **VAR**
- `frontend/vite.config.ts`: **VAR**
- `frontend/.env`: **YOK**
- `frontend/.env.example`: **VAR**
- `firebase.json`: **YOK**
- `.firebaserc`: **YOK**
- `Dockerfile`: **YOK**
- `backend/Dockerfile`: **YOK**
- `.gitignore`: **VAR**

## Ortam Değişkeni Anahtarları

### backend/.env

- `MISSIO_APP_NAME`
- `MISSIO_ENVIRONMENT`
- `MISSIO_DEBUG`
- `MISSIO_DEFAULT_TIMEZONE`
- `MISSIO_DATABASE_URL`
- `MISSIO_SECRET_KEY`
- `MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES`

### backend/.env.example

- `MISSIO_APP_NAME`
- `MISSIO_ENVIRONMENT`
- `MISSIO_DEBUG`
- `MISSIO_DEFAULT_TIMEZONE`
- `MISSIO_DATABASE_URL`
- `MISSIO_SECRET_KEY`
- `MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES`
- `MISSIO_RATE_LIMIT_ENABLED`
- `MISSIO_RATE_LIMIT_MAX_REQUESTS`
- `MISSIO_RATE_LIMIT_WINDOW_SECONDS`

### frontend/.env

Dosya yok.

### frontend/.env.example

- `VITE_API_BASE_URL`

## Cloud İçin Kritik Anahtar Kelime Kontrolü

### backend/app/core/config.py

- `DATABASE_URL`
- `SECRET_KEY`
- `DEBUG`
- `ENV`
- `PORT`

### backend/app/main.py

- `CORS`
- `middleware`
- `include_router`

### frontend/src/config/api.ts

- `API_BASE_URL`

### frontend/vite.config.ts

- `PWA`
- `VitePWA`
- `manifest`

## Dosya Önizlemeleri

### backend/app/core/config.py

```text
001: from functools import lru_cache
002: 
003: from pydantic import Field
004: from pydantic_settings import BaseSettings, SettingsConfigDict
005: 
006: 
007: class Settings(BaseSettings):
008:     """Application settings loaded from environment variables."""
009: 
010:     app_name: str = Field(default="Missio", alias="MISSIO_APP_NAME")
011:     environment: str = Field(default="local", alias="MISSIO_ENVIRONMENT")
012:     debug: bool = Field(default=True, alias="MISSIO_DEBUG")
013:     default_timezone: str = Field(
014:         default="Europe/Istanbul",
015:         alias="MISSIO_DEFAULT_TIMEZONE",
016:     )
017:     database_url: str = Field(
018:         default="sqlite:///./missio_local.db",
019:         alias="MISSIO_DATABASE_URL",
020:     )
021:     secret_key: str = Field(
022:         default="change-this-secret-key-before-production",
023:         alias="MISSIO_SECRET_KEY",
024:     )
025:     access_token_expire_minutes: int = Field(
026:         default=60,
027:         alias="MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES",
028:     )
029:     rate_limit_enabled: bool = Field(
030:         default=True,
031:         alias="MISSIO_RATE_LIMIT_ENABLED",
032:     )
033:     rate_limit_max_requests: int = Field(
034:         default=120,
035:         alias="MISSIO_RATE_LIMIT_MAX_REQUESTS",
036:     )
037:     rate_limit_window_seconds: int = Field(
038:         default=60,
039:         alias="MISSIO_RATE_LIMIT_WINDOW_SECONDS",
040:     )
041: 
042:     model_config = SettingsConfigDict(
043:         env_file=".env",
044:         env_file_encoding="utf-8",
045:         extra="ignore",
046:     )
047: 
048: 
049: @lru_cache
050: def get_settings() -> Settings:
051:     """Return cached application settings."""
052: 
053:     return Settings()
054: 
055: 
056: settings = get_settings()
```

### backend/app/main.py

```text
001: from fastapi import FastAPI
002: from fastapi.middleware.cors import CORSMiddleware
003: 
004: from app.api.router import api_router
005: from app.core.config import settings
006: from app.core.http_security import add_security_headers
007: from app.core.rate_limit import add_rate_limit
008: from app.core.security_config import is_production_environment
009: 
010: 
011: def create_app() -> FastAPI:
012:     """Create and configure the FastAPI application."""
013: 
014:     is_production = is_production_environment(settings.environment)
015: 
016:     app = FastAPI(
017:         title=settings.app_name,
018:         debug=settings.debug,
019:         version="0.1.0",
020:         description="Missio - Mission is possible.",
021:         docs_url=None if is_production else "/docs",
022:         redoc_url=None if is_production else "/redoc",
023:         openapi_url=None if is_production else "/openapi.json",
024:     )
025: 
026:     app.middleware("http")(add_security_headers)
027:     app.middleware("http")(add_rate_limit)
028: 
029:     local_development_origins = [
030:         "http://localhost:5173",
031:         "http://127.0.0.1:5173",
032:         "http://localhost:5174",
033:         "http://127.0.0.1:5174",
034:         "http://localhost:5175",
035:         "http://127.0.0.1:5175",
036:     ]
037: 
038:     local_network_origin_regex = (
039:         r"^http://("
040:         r"192\.168\.\d{1,3}\.\d{1,3}|"
041:         r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
042:         r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
043:         r"):(5173|5174|5175)$"
044:     )
045: 
046:     app.add_middleware(
047:         CORSMiddleware,
048:         allow_origins=[] if is_production else local_development_origins,
049:         allow_origin_regex=None if is_production else local_network_origin_regex,
050:         allow_credentials=True,
051:         allow_methods=["*"],
052:         allow_headers=["*"],
053:     )
054: 
055:     app.include_router(api_router)
056: 
057:     @app.get("/")
058:     def root() -> dict[str, str]:
059:         return {
060:             "message": "Missio backend is running.",
061:             "slogan": "Mission is possible.",
062:         }
063: 
064:     return app
065: 
066: 
067: app = create_app()
```

### backend/app/db/session.py

```text
001: from collections.abc import Generator
002: 
003: from sqlalchemy import create_engine, text
004: from sqlalchemy.orm import Session, sessionmaker
005: 
006: from app.core.config import settings
007: from app.db.sqlite import register_sqlite_pragmas
008: 
009: connect_args: dict[str, bool] = {}
010: 
011: if settings.database_url.startswith("sqlite"):
012:     connect_args = {"check_same_thread": False}
013: 
014: engine = create_engine(
015:     settings.database_url,
016:     connect_args=connect_args,
017:     pool_pre_ping=True,
018: )
019: 
020: register_sqlite_pragmas(engine)
021: 
022: SessionLocal = sessionmaker(
023:     autocommit=False,
024:     autoflush=False,
025:     bind=engine,
026: )
027: 
028: 
029: def get_db() -> Generator[Session, None, None]:
030:     """Provide a database session for FastAPI dependencies."""
031: 
032:     db = SessionLocal()
033: 
034:     try:
035:         yield db
036:     finally:
037:         db.close()
038: 
039: 
040: def check_database_connection() -> dict[str, str]:
041:     """Run a minimal database connection check."""
042: 
043:     with engine.connect() as connection:
044:         result = connection.execute(text("SELECT 1")).scalar_one()
045: 
046:     return {
047:         "status": "ok",
048:         "database": engine.url.get_backend_name(),
049:         "result": str(result),
050:     }
051: 
052: 
053: def get_sqlite_runtime_settings() -> dict[str, str]:
054:     """Return important SQLite runtime settings for diagnostics."""
055: 
056:     if not settings.database_url.startswith("sqlite"):
057:         return {
058:             "database": engine.url.get_backend_name(),
059:             "message": "SQLite runtime settings are not applicable.",
060:         }
061: 
062:     with engine.connect() as connection:
063:         foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
064:         journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()
065:         synchronous = connection.execute(text("PRAGMA synchronous")).scalar_one()
066:         busy_timeout = connection.execute(text("PRAGMA busy_timeout")).scalar_one()
067: 
068:     return {
069:         "database": "sqlite",
070:         "foreign_keys": str(foreign_keys),
071:         "journal_mode": str(journal_mode),
072:         "synchronous": str(synchronous),
073:         "busy_timeout": str(busy_timeout),
074:     }
```

### backend/app/db/base.py

```text
001: from sqlalchemy.orm import DeclarativeBase
002: 
003: 
004: class Base(DeclarativeBase):
005:     """Base class for all SQLAlchemy models."""
```

### backend/requirements.txt

```text
001: fastapi==0.115.6
002: uvicorn[standard]==0.34.0
003: pydantic==2.10.5
004: pydantic-settings==2.7.1
005: python-dotenv==1.0.1
006: SQLAlchemy==2.0.37
007: alembic==1.14.0
008: python-jose[cryptography]==3.3.0
009: python-multipart==0.0.20
010: pytest==8.3.4
011: httpx==0.28.1
012: bcrypt==4.0.1
013: tzdata==2025.2
014: Pillow==12.2.0
015: pillow-heif==1.3.0
016: reportlab==4.5.1
```

### backend/.env

```text
001: MISSIO_APP_NAME=Missio
002: MISSIO_ENVIRONMENT=local
003: MISSIO_DEBUG=true
004: MISSIO_DEFAULT_TIMEZONE=Europe/Istanbul
005: MISSIO_DATABASE_URL=***MASKED***
006: MISSIO_SECRET_KEY=***MASKED***
007: MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES=***MASKED***
```

### backend/.env.example

```text
001: MISSIO_APP_NAME=Missio
002: MISSIO_ENVIRONMENT=local
003: MISSIO_DEBUG=true
004: MISSIO_DEFAULT_TIMEZONE=Europe/Istanbul
005: MISSIO_DATABASE_URL=***MASKED***
006: MISSIO_SECRET_KEY=***MASKED***
007: MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES=***MASKED***
008: MISSIO_RATE_LIMIT_ENABLED=true
009: MISSIO_RATE_LIMIT_MAX_REQUESTS=120
010: MISSIO_RATE_LIMIT_WINDOW_SECONDS=60
```

### frontend/src/config/api.ts

```text
001: export const API_BASE_URL = "/api/v1"
002: 
003: export const ACCESS_TOKEN_STORAGE_KEY = "missio-access-token"
```

### frontend/package.json

```text
001: {
002:   "name": "frontend",
003:   "private": true,
004:   "version": "0.0.0",
005:   "type": "module",
006:   "scripts": {
007:     "dev": "vite",
008:     "build": "tsc -b && vite build",
009:     "lint": "eslint .",
010:     "preview": "vite preview"
011:   },
012:   "dependencies": {
013:     "@tailwindcss/vite": "^4.3.0",
014:     "lucide-react": "^1.16.0",
015:     "react": "^19.2.6",
016:     "react-dom": "^19.2.6",
017:     "tailwindcss": "^4.3.0"
018:   },
019:   "devDependencies": {
020:     "@eslint/js": "^10.0.1",
021:     "@types/node": "^24.12.3",
022:     "@types/react": "^19.2.14",
023:     "@types/react-dom": "^19.2.3",
024:     "@vitejs/plugin-react": "^6.0.1",
025:     "eslint": "^10.3.0",
026:     "eslint-plugin-react-hooks": "^7.1.1",
027:     "eslint-plugin-react-refresh": "^0.5.2",
028:     "globals": "^17.6.0",
029:     "typescript": "~6.0.2",
030:     "typescript-eslint": "^8.59.2",
031:     "vite": "^8.0.12",
032:     "vite-plugin-pwa": "^1.3.0"
033:   }
034: }
```

### frontend/vite.config.ts

```text
001: import { defineConfig } from 'vite'
002: import react from '@vitejs/plugin-react'
003: import tailwindcss from '@tailwindcss/vite'
004: import { VitePWA } from 'vite-plugin-pwa'
005: 
006: export default defineConfig({
007:   server: {
008:     host: '0.0.0.0',
009:     port: 5175,
010:     proxy: {
011:       '/api': {
012:         target: 'http://127.0.0.1:8000',
013:         changeOrigin: true,
014:         secure: false,
015:       },
016:     },
017:   },
018:   plugins: [
019:     react(),
020:     tailwindcss(),
021:     VitePWA({
022:       registerType: 'autoUpdate',
023:       includeAssets: ['favicon.svg', 'icons.svg'],
024:       manifest: {
025:         name: 'Missio',
026:         short_name: 'Missio',
027:         description: 'Mobil öncelikli işletme görev ve operasyon takip uygulaması.',
028:         theme_color: '#0f172a',
029:         background_color: '#f8fafc',
030:         display: 'standalone',
031:         orientation: 'portrait',
032:         scope: '/',
033:         start_url: '/',
034:         icons: [
035:           {
036:             src: '/icons.svg',
037:             sizes: '192x192',
038:             type: 'image/svg+xml',
039:             purpose: 'any',
040:           },
041:           {
042:             src: '/icons.svg',
043:             sizes: '512x512',
044:             type: 'image/svg+xml',
045:             purpose: 'maskable',
046:           },
047:         ],
048:       },
049:       workbox: {
050:         cleanupOutdatedCaches: true,
051:         clientsClaim: true,
052:         skipWaiting: true,
053:       },
054:       devOptions: {
055:         enabled: false,
056:       },
057:     }),
058:   ],
059: })
```

### frontend/.env.example

```text
001: VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### .gitignore

```text
001: # Python
002: __pycache__/
003: *.py[cod]
004: *.pyo
005: *.pyd
006: .Python
007: .venv/
008: venv/
009: env/
010: ENV/
011: pip-wheel-metadata/
012: .pytest_cache/
013: .mypy_cache/
014: .ruff_cache/
015: 
016: # FastAPI / backend local files
017: backend/.env
018: backend/.env.*
019: backend/app.db
020: backend/*.db
021: backend/*.sqlite
022: backend/*.sqlite3
023: backend/missio_local.db
024: missio_local.db
025: 
026: # Runtime storage files
027: backend/storage/
028: backend/storage/**
029: storage/uploads/*
030: storage/reports/*
031: storage/backups/*
032: storage/task_attachments/*
033: storage/task_attachments/**
034: 
035: # Keep storage folders
036: !storage/uploads/.gitkeep
037: !storage/uploads/tasks/.gitkeep
038: !storage/reports/.gitkeep
039: !storage/backups/.gitkeep
040: 
041: # Alembic / logs
042: *.log
043: logs/
044: 
045: # Node / frontend
046: node_modules/
047: frontend/node_modules/
048: frontend/dist/
049: frontend/.env
050: frontend/.env.*
051: frontend/.vite/
052: 
053: # Build outputs
054: build/
055: dist/
056: 
057: # OS / editor
058: .DS_Store
059: Thumbs.db
060: .vscode/
061: .idea/
062: 
063: # Secrets
064: *.pem
065: *.key
066: *.crt
067: *.pfx
068: *.p12
069: 
070: # Local one-off setup helper scripts
071: /ADIM_*.py
072: /ADIM_*.ps1
073: *.db-wal
074: *.db-shm
075: *.pyc
076: temp/
077: tmp/
078: 
079: # Local database backups
080: backend/_db_backup/
... (2 satır daha var)
```

