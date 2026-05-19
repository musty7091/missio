from __future__ import annotations

import app.models  # noqa: F401
from app.db.seeds import seed_database
from app.db.session import SessionLocal


def main() -> None:
    """Run Missio database seed operation."""

    db = SessionLocal()

    try:
        result = seed_database(db)
    finally:
        db.close()

    print("Missio seed işlemi tamamlandı.")
    print(f"app_settings: {result['app_settings']}")
    print(f"packages: {result['packages']}")
    print(f"modules: {result['modules']}")


if __name__ == "__main__":
    main()
