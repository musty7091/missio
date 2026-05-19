from __future__ import annotations

import sys

from app.core.config import settings
from app.core.security_config import validate_runtime_security_settings


def main() -> None:
    """Run runtime security configuration checks."""

    report = validate_runtime_security_settings(
        environment=settings.environment,
        debug=settings.debug,
        secret_key=settings.secret_key,
        database_url=settings.database_url,
        default_timezone=settings.default_timezone,
    )

    print("Missio production güvenlik ayar kontrolü")
    print(f"Environment: {report.environment}")
    print(f"Production modu: {'Evet' if report.is_production else 'Hayır'}")
    print("")

    for result in report.results:
        print(f"[{result.status}] {result.name}: {result.message}")

    print("")

    if report.has_failures:
        print("Production güvenlik ayar kontrolü başarısız.")
        sys.exit(1)

    if report.has_warnings:
        print("Production güvenlik ayar kontrolü uyarılarla tamamlandı.")
        return

    print("Production güvenlik ayar kontrolü başarılı.")


if __name__ == "__main__":
    main()
