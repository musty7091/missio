from __future__ import annotations

from pathlib import Path
import py_compile

ROOT_DIR = Path(r"C:\missio")
SECURITY_CHECKLIST_PATH = ROOT_DIR / "docs" / "SECURITY_CHECKLIST.md"

FILES = {'backend/app/core/security_config.py': 'from __future__ import annotations\n\nfrom dataclasses import dataclass\n\n\nWEAK_SECRET_KEY_VALUES = {\n    "",\n    "secret",\n    "secret-key",\n    "change-me",\n    "change-this-secret-key-before-production",\n    "development",\n    "password",\n    "missio",\n}\n\nWEAK_SECRET_KEY_PARTS = {\n    "change-this",\n    "before-production",\n    "changeme",\n    "default",\n    "example",\n    "password",\n}\n\nMINIMUM_PRODUCTION_SECRET_KEY_LENGTH = 32\n\n\n@dataclass(frozen=True)\nclass SecurityCheckResult:\n    """Single runtime security check result."""\n\n    name: str\n    status: str\n    message: str\n\n\n@dataclass(frozen=True)\nclass RuntimeSecurityReport:\n    """Runtime security validation report."""\n\n    environment: str\n    is_production: bool\n    results: list[SecurityCheckResult]\n\n    @property\n    def has_failures(self) -> bool:\n        """Return whether the report contains FAIL entries."""\n\n        return any(result.status == "FAIL" for result in self.results)\n\n    @property\n    def has_warnings(self) -> bool:\n        """Return whether the report contains WARN entries."""\n\n        return any(result.status == "WARN" for result in self.results)\n\n\ndef normalize_environment(environment: str) -> str:\n    """Normalize environment name."""\n\n    return environment.strip().lower()\n\n\ndef is_production_environment(environment: str) -> bool:\n    """Return whether the environment should be treated as production."""\n\n    return normalize_environment(environment) in {\n        "prod",\n        "production",\n        "live",\n    }\n\n\ndef is_secret_key_strong(secret_key: str) -> bool:\n    """Return whether a secret key is acceptable for production."""\n\n    normalized_secret = secret_key.strip()\n    lowered_secret = normalized_secret.lower()\n\n    if lowered_secret in WEAK_SECRET_KEY_VALUES:\n        return False\n\n    if len(normalized_secret) < MINIMUM_PRODUCTION_SECRET_KEY_LENGTH:\n        return False\n\n    return not any(part in lowered_secret for part in WEAK_SECRET_KEY_PARTS)\n\n\ndef check_secret_key(secret_key: str, is_production: bool) -> SecurityCheckResult:\n    """Validate secret key strength."""\n\n    if is_secret_key_strong(secret_key):\n        return SecurityCheckResult(\n            name="secret_key",\n            status="OK",\n            message="SECRET_KEY production için yeterli görünüyor.",\n        )\n\n    if is_production:\n        return SecurityCheckResult(\n            name="secret_key",\n            status="FAIL",\n            message=(\n                "Production ortamda zayıf veya varsayılan SECRET_KEY kullanılamaz."\n            ),\n        )\n\n    return SecurityCheckResult(\n        name="secret_key",\n        status="WARN",\n        message=(\n            "Local ortamda zayıf SECRET_KEY kullanılabilir, "\n            "production için değiştirilmelidir."\n        ),\n    )\n\n\ndef check_debug(debug: bool, is_production: bool) -> SecurityCheckResult:\n    """Validate debug setting."""\n\n    if is_production and debug:\n        return SecurityCheckResult(\n            name="debug",\n            status="FAIL",\n            message="Production ortamda DEBUG açık olamaz.",\n        )\n\n    if debug:\n        return SecurityCheckResult(\n            name="debug",\n            status="WARN",\n            message="DEBUG local geliştirme için açık.",\n        )\n\n    return SecurityCheckResult(\n        name="debug",\n        status="OK",\n        message="DEBUG kapalı.",\n    )\n\n\ndef check_database_url(database_url: str, is_production: bool) -> SecurityCheckResult:\n    """Validate database URL for accidental unsafe values."""\n\n    normalized_url = database_url.strip().lower()\n\n    if not normalized_url:\n        return SecurityCheckResult(\n            name="database_url",\n            status="FAIL",\n            message="DATABASE_URL boş olamaz.",\n        )\n\n    if is_production and normalized_url.startswith("sqlite:///./"):\n        return SecurityCheckResult(\n            name="database_url",\n            status="WARN",\n            message=(\n                "Production ortamda göreli SQLite yolu kullanılıyor. "\n                "Müşteri bazlı kurulum için kabul edilebilir, fakat "\n                "yedekleme ve dosya yetkileri ayrıca kontrol edilmelidir."\n            ),\n        )\n\n    return SecurityCheckResult(\n        name="database_url",\n        status="OK",\n        message="DATABASE_URL temel kontrolü başarılı.",\n    )\n\n\ndef check_timezone(default_timezone: str) -> SecurityCheckResult:\n    """Validate timezone setting."""\n\n    if not default_timezone.strip():\n        return SecurityCheckResult(\n            name="default_timezone",\n            status="FAIL",\n            message="Timezone boş olamaz.",\n        )\n\n    return SecurityCheckResult(\n        name="default_timezone",\n        status="OK",\n        message="Timezone tanımlı.",\n    )\n\n\ndef validate_runtime_security_settings(\n    *,\n    environment: str,\n    debug: bool,\n    secret_key: str,\n    database_url: str,\n    default_timezone: str,\n) -> RuntimeSecurityReport:\n    """Validate important runtime security settings."""\n\n    normalized_environment = normalize_environment(environment)\n    is_production = is_production_environment(normalized_environment)\n\n    results = [\n        check_debug(debug=debug, is_production=is_production),\n        check_secret_key(secret_key=secret_key, is_production=is_production),\n        check_database_url(\n            database_url=database_url,\n            is_production=is_production,\n        ),\n        check_timezone(default_timezone=default_timezone),\n    ]\n\n    return RuntimeSecurityReport(\n        environment=normalized_environment,\n        is_production=is_production,\n        results=results,\n    )\n', 'backend/app/commands/check_production_security.py': 'from __future__ import annotations\n\nimport sys\n\nfrom app.core.config import settings\nfrom app.core.security_config import validate_runtime_security_settings\n\n\ndef main() -> None:\n    """Run runtime security configuration checks."""\n\n    report = validate_runtime_security_settings(\n        environment=settings.environment,\n        debug=settings.debug,\n        secret_key=settings.secret_key,\n        database_url=settings.database_url,\n        default_timezone=settings.default_timezone,\n    )\n\n    print("Missio production güvenlik ayar kontrolü")\n    print(f"Environment: {report.environment}")\n    print(f"Production modu: {\'Evet\' if report.is_production else \'Hayır\'}")\n    print("")\n\n    for result in report.results:\n        print(f"[{result.status}] {result.name}: {result.message}")\n\n    print("")\n\n    if report.has_failures:\n        print("Production güvenlik ayar kontrolü başarısız.")\n        sys.exit(1)\n\n    if report.has_warnings:\n        print("Production güvenlik ayar kontrolü uyarılarla tamamlandı.")\n        return\n\n    print("Production güvenlik ayar kontrolü başarılı.")\n\n\nif __name__ == "__main__":\n    main()\n', 'backend/tests/test_security_config.py': 'from app.core.security_config import (\n    is_secret_key_strong,\n    validate_runtime_security_settings,\n)\n\n\ndef test_secret_key_rejects_default_value() -> None:\n    assert not is_secret_key_strong("change-this-secret-key-before-production")\n\n\ndef test_secret_key_rejects_short_value() -> None:\n    assert not is_secret_key_strong("short")\n\n\ndef test_secret_key_accepts_strong_value() -> None:\n    assert is_secret_key_strong(\n        "Missio_Production_Secret_Key_2026_With_Strong_Length!"\n    )\n\n\ndef test_production_debug_enabled_fails() -> None:\n    report = validate_runtime_security_settings(\n        environment="production",\n        debug=True,\n        secret_key="Missio_Production_Secret_Key_2026_With_Strong_Length!",\n        database_url="sqlite:///C:/missio/data/missio.db",\n        default_timezone="Europe/Istanbul",\n    )\n\n    assert report.has_failures\n    assert any(\n        result.name == "debug" and result.status == "FAIL"\n        for result in report.results\n    )\n\n\ndef test_production_default_secret_fails() -> None:\n    report = validate_runtime_security_settings(\n        environment="production",\n        debug=False,\n        secret_key="change-this-secret-key-before-production",\n        database_url="sqlite:///C:/missio/data/missio.db",\n        default_timezone="Europe/Istanbul",\n    )\n\n    assert report.has_failures\n    assert any(\n        result.name == "secret_key" and result.status == "FAIL"\n        for result in report.results\n    )\n\n\ndef test_local_default_secret_warns_but_does_not_fail() -> None:\n    report = validate_runtime_security_settings(\n        environment="local",\n        debug=True,\n        secret_key="change-this-secret-key-before-production",\n        database_url="sqlite:///./missio_local.db",\n        default_timezone="Europe/Istanbul",\n    )\n\n    assert not report.has_failures\n    assert report.has_warnings\n'}

CHECKLIST_REPLACEMENTS = {
    "- [ ] Production ortamda zayıf `SECRET_KEY` ile uygulama açılmayacak.": "- [x] Production ortamda zayıf `SECRET_KEY` ile uygulama açılmayacak.",
    "- [ ] Production ortamda güçlü `SECRET_KEY` zorunlu olacak.": "- [x] Production ortamda güçlü `SECRET_KEY` zorunlu olacak.",
    "- [ ] Production ortamda debug kapalı olacak.": "- [x] Production ortamda debug kapalı olacak.",
    "- [ ] Production güvenlik kontrol komutu yazılacak.": "- [x] Production güvenlik kontrol komutu yazılacak.",
}


def write_file(relative_path: str, content: str) -> None:
    target = ROOT_DIR / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"Yazildi: {target}")


def update_security_checklist() -> None:
    if not SECURITY_CHECKLIST_PATH.exists():
        print("SECURITY_CHECKLIST.md bulunamadi, atlandi.")
        return

    content = SECURITY_CHECKLIST_PATH.read_text(encoding="utf-8")

    for old, new in CHECKLIST_REPLACEMENTS.items():
        content = content.replace(old, new)

    SECURITY_CHECKLIST_PATH.write_text(content, encoding="utf-8")
    print("SECURITY_CHECKLIST.md guncellendi.")


def compile_files() -> None:
    for relative_path in FILES:
        if relative_path.endswith(".py"):
            py_compile.compile(str(ROOT_DIR / relative_path), doraise=True)

    print("Python syntax kontrolu basarili.")


def main() -> None:
    print("Missio ADIM 5G production guvenlik ayar kontrolu olusturuluyor.")
    print("")

    for relative_path, content in FILES.items():
        write_file(relative_path, content)

    update_security_checklist()
    compile_files()

    print("")
    print("Tamamlandi.")


if __name__ == "__main__":
    main()
