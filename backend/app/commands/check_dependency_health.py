from __future__ import annotations

import importlib.metadata
import sys
from pathlib import Path


REQUIRED_PACKAGES = [
    "fastapi",
    "sqlalchemy",
    "alembic",
    "bcrypt",
    "python-jose",
    "pydantic",
    "pydantic-settings",
    "pytest",
]

FORBIDDEN_APP_IMPORTS = [
    "passlib",
]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def get_package_version(package_name: str) -> str:
    """Return installed package version."""

    return importlib.metadata.version(package_name)


def check_required_packages() -> None:
    """Check required packages are importable through metadata."""

    print("Zorunlu paket sürüm kontrolü:")

    for package_name in REQUIRED_PACKAGES:
        version = get_package_version(package_name)
        print(f"- {package_name}: {version}")

    print("Zorunlu paket sürüm kontrolü başarılı.")


def check_bcrypt_runtime() -> None:
    """Check bcrypt hashing and verification work without passlib."""

    import bcrypt

    password = "Missio.2026!"
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    )

    if password.encode("utf-8") in password_hash:
        raise RuntimeError("bcrypt hash içinde açık şifre görünüyor.")

    if not bcrypt.checkpw(password.encode("utf-8"), password_hash):
        raise RuntimeError("bcrypt doğru şifreyi doğrulayamadı.")

    if bcrypt.checkpw("Wrong.2026!".encode("utf-8"), password_hash):
        raise RuntimeError("bcrypt yanlış şifreyi kabul etti.")

    print("bcrypt runtime kontrolü başarılı.")


def find_forbidden_imports() -> list[str]:
    """Find forbidden imports in application source files."""

    findings: list[str] = []
    search_roots = [
        BACKEND_ROOT / "app",
        BACKEND_ROOT / "tests",
    ]

    for search_root in search_roots:
        if not search_root.exists():
            continue

        for path in search_root.rglob("*.py"):
            content = path.read_text(encoding="utf-8")

            for forbidden_import in FORBIDDEN_APP_IMPORTS:
                if f"import {forbidden_import}" in content:
                    findings.append(str(path.relative_to(PROJECT_ROOT)))
                if f"from {forbidden_import}" in content:
                    findings.append(str(path.relative_to(PROJECT_ROOT)))

    return sorted(set(findings))


def check_no_forbidden_imports() -> None:
    """Ensure removed dependencies are not imported by app code."""

    findings = find_forbidden_imports()

    if findings:
        print("Yasaklı dependency importları bulundu:")
        for finding in findings:
            print(f"- {finding}")

        raise RuntimeError("Yasaklı dependency importları temizlenmelidir.")

    print("passlib import temizliği başarılı.")


def check_active_python() -> None:
    """Print active interpreter information."""

    print(f"Aktif Python: {sys.executable}")

    if sys.prefix == sys.base_prefix:
        print("UYARI: Aktif ortam venv gibi görünmüyor.")
    else:
        print("Aktif ortam venv olarak görünüyor.")


def main() -> None:
    """Run Missio dependency health checks."""

    print("Missio dependency health kontrolü başlıyor.")

    check_active_python()
    check_required_packages()
    check_bcrypt_runtime()
    check_no_forbidden_imports()

    print("Dependency health kontrolü başarılı.")


if __name__ == "__main__":
    main()
