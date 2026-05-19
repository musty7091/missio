from __future__ import annotations

import sys

from sqlalchemy import inspect

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


EXPECTED_TABLES = {
    "alembic_version",
    "app_settings",
    "audit_logs",
    "business_features",
    "business_modules",
    "businesses",
    "consent_documents",
    "daily_reports",
    "licenses",
    "modules",
    "notifications",
    "packages",
    "setup_state",
    "task_attachments",
    "task_categories",
    "task_events",
    "task_templates",
    "tasks",
    "user_consents",
    "users",
}


def main() -> None:
    """Validate that database tables and model metadata are aligned."""

    inspector = inspect(engine)
    database_tables = set(inspector.get_table_names())
    model_tables = set(Base.metadata.tables.keys())

    missing_in_database = sorted(EXPECTED_TABLES - database_tables)
    missing_in_models = sorted((EXPECTED_TABLES - {"alembic_version"}) - model_tables)

    print(f"Model tablo sayısı: {len(model_tables)}")
    print(f"Veritabanı tablo sayısı: {len(database_tables)}")
    print("")

    print("Model tabloları:")
    for table_name in sorted(model_tables):
        print(f"- {table_name}")

    print("")
    print("Veritabanı tabloları:")
    for table_name in sorted(database_tables):
        print(f"- {table_name}")

    if missing_in_database or missing_in_models:
        print("")
        print("Baseline kontrolü başarısız.")

        if missing_in_database:
            print("Veritabanında eksik tablolar:")
            for table_name in missing_in_database:
                print(f"- {table_name}")

        if missing_in_models:
            print("Model metadata içinde eksik tablolar:")
            for table_name in missing_in_models:
                print(f"- {table_name}")

        sys.exit(1)

    print("")
    print("Baseline kontrolü başarılı.")


if __name__ == "__main__":
    main()
