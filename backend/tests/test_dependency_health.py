from pathlib import Path

from app.commands import check_dependency_health
from app.core.security import hash_password, verify_password


def test_bcrypt_hash_and_verify_without_passlib() -> None:
    password = "Missio.2026!"
    password_hash = hash_password(password)

    assert password not in password_hash
    assert verify_password(password, password_hash)
    assert not verify_password("Wrong.2026!", password_hash)


def test_dependency_health_required_packages_are_declared() -> None:
    assert "bcrypt" in check_dependency_health.REQUIRED_PACKAGES
    assert "passlib" not in check_dependency_health.REQUIRED_PACKAGES


def test_dependency_health_forbidden_import_scan() -> None:
    findings = check_dependency_health.find_forbidden_imports()

    assert findings == []


def test_requirements_does_not_include_passlib() -> None:
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    content = requirements_path.read_text(encoding="utf-8").lower()

    assert "passlib" not in content


def test_requirements_includes_bcrypt_pin() -> None:
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    content = requirements_path.read_text(encoding="utf-8").lower()

    assert "bcrypt==" in content
