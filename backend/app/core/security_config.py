from __future__ import annotations

from dataclasses import dataclass


WEAK_SECRET_KEY_VALUES = {
    "",
    "secret",
    "secret-key",
    "change-me",
    "change-this-secret-key-before-production",
    "development",
    "password",
    "missio",
}

WEAK_SECRET_KEY_PARTS = {
    "change-this",
    "before-production",
    "changeme",
    "default",
    "example",
    "password",
}

MINIMUM_PRODUCTION_SECRET_KEY_LENGTH = 32


@dataclass(frozen=True)
class SecurityCheckResult:
    """Single runtime security check result."""

    name: str
    status: str
    message: str


@dataclass(frozen=True)
class RuntimeSecurityReport:
    """Runtime security validation report."""

    environment: str
    is_production: bool
    results: list[SecurityCheckResult]

    @property
    def has_failures(self) -> bool:
        """Return whether the report contains FAIL entries."""

        return any(result.status == "FAIL" for result in self.results)

    @property
    def has_warnings(self) -> bool:
        """Return whether the report contains WARN entries."""

        return any(result.status == "WARN" for result in self.results)


def normalize_environment(environment: str) -> str:
    """Normalize environment name."""

    return environment.strip().lower()


def is_production_environment(environment: str) -> bool:
    """Return whether the environment should be treated as production."""

    return normalize_environment(environment) in {
        "prod",
        "production",
        "live",
    }


def is_secret_key_strong(secret_key: str) -> bool:
    """Return whether a secret key is acceptable for production."""

    normalized_secret = secret_key.strip()
    lowered_secret = normalized_secret.lower()

    if lowered_secret in WEAK_SECRET_KEY_VALUES:
        return False

    if len(normalized_secret) < MINIMUM_PRODUCTION_SECRET_KEY_LENGTH:
        return False

    return not any(part in lowered_secret for part in WEAK_SECRET_KEY_PARTS)


def check_secret_key(secret_key: str, is_production: bool) -> SecurityCheckResult:
    """Validate secret key strength."""

    if is_secret_key_strong(secret_key):
        return SecurityCheckResult(
            name="secret_key",
            status="OK",
            message="SECRET_KEY production için yeterli görünüyor.",
        )

    if is_production:
        return SecurityCheckResult(
            name="secret_key",
            status="FAIL",
            message=(
                "Production ortamda zayıf veya varsayılan SECRET_KEY kullanılamaz."
            ),
        )

    return SecurityCheckResult(
        name="secret_key",
        status="WARN",
        message=(
            "Local ortamda zayıf SECRET_KEY kullanılabilir, "
            "production için değiştirilmelidir."
        ),
    )


def check_debug(debug: bool, is_production: bool) -> SecurityCheckResult:
    """Validate debug setting."""

    if is_production and debug:
        return SecurityCheckResult(
            name="debug",
            status="FAIL",
            message="Production ortamda DEBUG açık olamaz.",
        )

    if debug:
        return SecurityCheckResult(
            name="debug",
            status="WARN",
            message="DEBUG local geliştirme için açık.",
        )

    return SecurityCheckResult(
        name="debug",
        status="OK",
        message="DEBUG kapalı.",
    )


def check_database_url(database_url: str, is_production: bool) -> SecurityCheckResult:
    """Validate database URL for accidental unsafe values."""

    normalized_url = database_url.strip().lower()

    if not normalized_url:
        return SecurityCheckResult(
            name="database_url",
            status="FAIL",
            message="DATABASE_URL boş olamaz.",
        )

    if is_production and normalized_url.startswith("sqlite:///./"):
        return SecurityCheckResult(
            name="database_url",
            status="WARN",
            message=(
                "Production ortamda göreli SQLite yolu kullanılıyor. "
                "Müşteri bazlı kurulum için kabul edilebilir, fakat "
                "yedekleme ve dosya yetkileri ayrıca kontrol edilmelidir."
            ),
        )

    return SecurityCheckResult(
        name="database_url",
        status="OK",
        message="DATABASE_URL temel kontrolü başarılı.",
    )


def check_timezone(default_timezone: str) -> SecurityCheckResult:
    """Validate timezone setting."""

    if not default_timezone.strip():
        return SecurityCheckResult(
            name="default_timezone",
            status="FAIL",
            message="Timezone boş olamaz.",
        )

    return SecurityCheckResult(
        name="default_timezone",
        status="OK",
        message="Timezone tanımlı.",
    )


def validate_runtime_security_settings(
    *,
    environment: str,
    debug: bool,
    secret_key: str,
    database_url: str,
    default_timezone: str,
) -> RuntimeSecurityReport:
    """Validate important runtime security settings."""

    normalized_environment = normalize_environment(environment)
    is_production = is_production_environment(normalized_environment)

    results = [
        check_debug(debug=debug, is_production=is_production),
        check_secret_key(secret_key=secret_key, is_production=is_production),
        check_database_url(
            database_url=database_url,
            is_production=is_production,
        ),
        check_timezone(default_timezone=default_timezone),
    ]

    return RuntimeSecurityReport(
        environment=normalized_environment,
        is_production=is_production,
        results=results,
    )
