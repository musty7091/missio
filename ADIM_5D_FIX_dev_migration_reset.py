from __future__ import annotations

from pathlib import Path
import shutil

ROOT_DIR = Path(r"C:\missio")
BACKEND_DIR = ROOT_DIR / "backend"
VERSIONS_DIR = BACKEND_DIR / "alembic" / "versions"

DATABASE_FILES = [
    BACKEND_DIR / "missio_local.db",
    BACKEND_DIR / "missio_local.db-wal",
    BACKEND_DIR / "missio_local.db-shm",
]


def delete_local_database_files() -> None:
    for path in DATABASE_FILES:
        if path.exists():
            path.unlink()
            print(f"Silindi: {path}")
        else:
            print(f"Yok, atlandi: {path}")


def delete_old_migration_files() -> None:
    if not VERSIONS_DIR.exists():
        raise FileNotFoundError(f"Alembic versions klasoru bulunamadi: {VERSIONS_DIR}")

    for path in sorted(VERSIONS_DIR.glob("*.py")):
        path.unlink()
        print(f"Silindi: {path}")

    for path in sorted(VERSIONS_DIR.glob("*.pyc")):
        path.unlink()
        print(f"Silindi: {path}")

    pycache_dir = VERSIONS_DIR / "__pycache__"

    if pycache_dir.exists():
        shutil.rmtree(pycache_dir)
        print(f"Silindi: {pycache_dir}")

    gitkeep = VERSIONS_DIR / ".gitkeep"

    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
        print(f"Olusturuldu: {gitkeep}")


def main() -> None:
    print("Missio development migration reset basladi.")
    print("")
    print("Bu islem sadece lokal gelistirme ortami icindir.")
    print("Canli musteri verisi icin kullanilmaz.")
    print("")

    delete_local_database_files()
    delete_old_migration_files()

    print("")
    print("Temizlik tamamlandi.")
    print("")
    print("Simdi C:\\missio\\backend icinde su komutlari calistir:")
    print("")
    print('python -m alembic revision --autogenerate -m "full baseline schema"')
    print("python -m alembic upgrade head")
    print("python -m app.commands.check_baseline")
    print("python -m app.commands.seed_database")
    print("python -m app.commands.check_login_security")
    print("python -m pytest tests/test_login_security.py tests/test_auth_service.py")
    print("")
    print("Beklenen tablo sayilari:")
    print("Model tablo sayisi: 20")
    print("Veritabani tablo sayisi: 21")
    print("")
    print("Not: 21. tablo Alembic'in alembic_version tablosudur.")


if __name__ == "__main__":
    main()
