# Missio - ADIM 4B
# Alembic migration altyapisini kurar ve SQLite ayarlariyla uyumlu hale getirir.
# Bu dosyayi C:\missio icinde calistir.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "C:\missio"

New-Item -ItemType Directory -Force -Path "backend\alembic" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\alembic\versions" | Out-Null

@'
[alembic]
script_location = alembic
prepend_sys_path = .
path_separator = os
sqlalchemy.url = sqlite:///./missio_local.db

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'@ | Set-Content -Encoding UTF8 "backend\alembic.ini"

@'
"""Alembic environment configuration for Missio."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    configuration = config.get_section(config.config_ini_section)

    if configuration is None:
        raise RuntimeError("Alembic configuration section could not be loaded.")

    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {},
    )

    with connectable.connect() as connection:
        if settings.database_url.startswith("sqlite"):
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.exec_driver_sql("PRAGMA journal_mode=WAL")
            connection.exec_driver_sql("PRAGMA synchronous=NORMAL")
            connection.exec_driver_sql("PRAGMA busy_timeout=5000")

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'@ | Set-Content -Encoding UTF8 "backend\alembic\env.py"

@'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Apply migration."""

    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Rollback migration."""

    ${downgrades if downgrades else "pass"}
'@ | Set-Content -Encoding UTF8 "backend\alembic\script.py.mako"

New-Item -ItemType File -Force -Path "backend\alembic\versions\.gitkeep" | Out-Null

Write-Host ""
Write-Host "ADIM 4B Alembic dosyalari olusturuldu." -ForegroundColor Green
Write-Host "Test icin su komutlari calistir:" -ForegroundColor Cyan
Write-Host ""
Write-Host "cd C:\missio\backend"
Write-Host ".\.venv\Scripts\activate"
Write-Host "alembic current"
Write-Host ""
Write-Host "Beklenen sonuc: Hata vermemeli. Henuz migration olmadigi icin bos donebilir."
Write-Host ""
