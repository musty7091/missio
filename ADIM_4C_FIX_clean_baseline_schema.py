from __future__ import annotations

from pathlib import Path
import py_compile

ROOT_DIR = Path(r"C:\missio")
BACKEND_DIR = ROOT_DIR / "backend"
MODELS_DIR = BACKEND_DIR / "app" / "models"
ALEMBIC_DIR = BACKEND_DIR / "alembic"
VERSIONS_DIR = ALEMBIC_DIR / "versions"

ENV_CONTENT = """\"\"\"Alembic environment configuration for Missio.\"\"\"

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    \"\"\"Run migrations in offline mode.\"\"\"

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
    \"\"\"Run migrations in online mode.\"\"\"

    configuration = config.get_section(config.config_ini_section)

    if configuration is None:
        raise RuntimeError("Alembic configuration section could not be loaded.")

    configuration["sqlalchemy.url"] = settings.database_url

    connect_args: dict[str, bool] = {}

    if settings.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
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
"""


def clean_model_files() -> None:
    if not MODELS_DIR.exists():
        raise FileNotFoundError(f"Model klasoru bulunamadi: {MODELS_DIR}")

    for path in sorted(MODELS_DIR.glob("*.py")):
        content = path.read_text(encoding="utf-8")

        # Onceki script bazi dosyalarin sonuna literal \n yazmis olabilir.
        # Python kodunda bu SyntaxError'a sebep olur. Gercek satir sonuna ceviriyoruz.
        content = content.replace("\\n", "\n")

        path.write_text(content, encoding="utf-8")
        print(f"Temizlendi: {path}")


def rewrite_alembic_env() -> None:
    env_path = ALEMBIC_DIR / "env.py"
    env_path.write_text(ENV_CONTENT, encoding="utf-8")
    print(f"Yeniden yazildi: {env_path}")


def remove_local_database() -> None:
    for file_name in [
        "missio_local.db",
        "missio_local.db-wal",
        "missio_local.db-shm",
    ]:
        path = BACKEND_DIR / file_name
        if path.exists():
            path.unlink()
            print(f"Silindi: {path}")


def remove_generated_revisions() -> None:
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(VERSIONS_DIR.glob("*.py")):
        path.unlink()
        print(f"Silindi: {path}")

    gitkeep = VERSIONS_DIR / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")


def compile_python_files() -> None:
    paths = list(MODELS_DIR.glob("*.py")) + [ALEMBIC_DIR / "env.py"]

    for path in paths:
        py_compile.compile(str(path), doraise=True)

    print("Python syntax kontrolu basarili.")


def main() -> None:
    print("Missio ADIM 4C baseline duzeltmesi basladi.")
    print("Bu islem sadece lokal gelistirme veritabanini ve bos migration'i temizler.")
    print("Canli veri olmadigi icin guvenlidir.")
    print("")

    clean_model_files()
    rewrite_alembic_env()
    remove_local_database()
    remove_generated_revisions()
    compile_python_files()

    print("")
    print("Duzeltme tamamlandi.")
    print("")
    print("Simdi su komutlari calistir:")
    print(r"cd C:\missio\backend")
    print(r"python -m alembic revision --autogenerate -m \"baseline schema\"")
    print(r"python -m alembic upgrade head")
    print(r"python -m alembic current")
    print(
        "python -c \"from sqlalchemy import inspect; "
        "from app.db.session import engine; "
        "tables = inspect(engine).get_table_names(); "
        "print(len(tables)); print('\\n'.join(tables))\""
    )


if __name__ == "__main__":
    main()
