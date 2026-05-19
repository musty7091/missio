from pathlib import Path

PROJECT_ROOT = Path(r"C:\missio")
ENV_PATH = PROJECT_ROOT / "backend" / "alembic" / "env.py"

env_content = '"""Alembic environment configuration for Missio."""\n\nfrom logging.config import fileConfig\n\nfrom alembic import context\nfrom sqlalchemy import engine_from_config, pool\n\nfrom app.core.config import settings\nfrom app.db.base import Base\n\nconfig = context.config\n\nif config.config_file_name is not None:\n    fileConfig(config.config_file_name)\n\nconfig.set_main_option("sqlalchemy.url", settings.database_url)\n\ntarget_metadata = Base.metadata\n\n\ndef run_migrations_offline() -> None:\n    """Run migrations in offline mode."""\n\n    url = config.get_main_option("sqlalchemy.url")\n\n    context.configure(\n        url=url,\n        target_metadata=target_metadata,\n        literal_binds=True,\n        dialect_opts={\n            "paramstyle": "named",\n        },\n        compare_type=True,\n    )\n\n    with context.begin_transaction():\n        context.run_migrations()\n\n\ndef run_migrations_online() -> None:\n    """Run migrations in online mode."""\n\n    configuration = config.get_section(config.config_ini_section)\n\n    if configuration is None:\n        raise RuntimeError("Alembic configuration section could not be loaded.")\n\n    configuration["sqlalchemy.url"] = settings.database_url\n\n    connect_args: dict[str, bool] = {}\n\n    if settings.database_url.startswith("sqlite"):\n        connect_args = {"check_same_thread": False}\n\n    connectable = engine_from_config(\n        configuration,\n        prefix="sqlalchemy.",\n        poolclass=pool.NullPool,\n        connect_args=connect_args,\n    )\n\n    with connectable.connect() as connection:\n        if settings.database_url.startswith("sqlite"):\n            connection.exec_driver_sql("PRAGMA foreign_keys=ON")\n            connection.exec_driver_sql("PRAGMA journal_mode=WAL")\n            connection.exec_driver_sql("PRAGMA synchronous=NORMAL")\n            connection.exec_driver_sql("PRAGMA busy_timeout=5000")\n\n        context.configure(\n            connection=connection,\n            target_metadata=target_metadata,\n            compare_type=True,\n        )\n\n        with context.begin_transaction():\n            context.run_migrations()\n\n\nif context.is_offline_mode():\n    run_migrations_offline()\nelse:\n    run_migrations_online()\n'

ENV_PATH.write_text(env_content, encoding="utf-8")

raw = ENV_PATH.read_bytes()
print("env.py temiz yazildi.")
print(f"Dosya: {ENV_PATH}")
print(f"Ilk 3 byte: {raw[:3]}")
print(f"Son 10 byte: {raw[-10:]}")
print("Sonraki test komutlari:")
print(r"cd C:\missio\backend")
print(r"python -m alembic revision --autogenerate -m \"baseline schema\"")
