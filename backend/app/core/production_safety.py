from __future__ import annotations


DEFAULT_DEVELOPMENT_SECRET_KEY = "change-this-secret-key-before-production"


def validate_production_settings(settings: object) -> None:
    """Validate dangerous settings before the app starts in production."""

    environment = str(getattr(settings, "environment", "") or "").strip().lower()

    if environment not in {"production", "prod"}:
        return

    errors: list[str] = []

    debug = bool(getattr(settings, "debug", False))
    secret_key = str(getattr(settings, "secret_key", "") or "").strip()
    database_url = str(getattr(settings, "database_url", "") or "").strip().lower()
    default_timezone = str(getattr(settings, "default_timezone", "") or "").strip()
    cors_allowed_origins = str(getattr(settings, "cors_allowed_origins", "") or "").strip()

    if debug:
        errors.append("MISSIO_DEBUG production ortamında false olmalıdır.")

    if not secret_key:
        errors.append("MISSIO_SECRET_KEY production ortamında boş olamaz.")
    elif secret_key == DEFAULT_DEVELOPMENT_SECRET_KEY:
        errors.append("MISSIO_SECRET_KEY varsayılan geliştirme değeriyle kalamaz.")
    elif len(secret_key) < 32:
        errors.append("MISSIO_SECRET_KEY production ortamında en az 32 karakter olmalıdır.")

    if not database_url:
        errors.append("MISSIO_DATABASE_URL production ortamında boş olamaz.")
    elif database_url.startswith("sqlite"):
        errors.append("MISSIO_DATABASE_URL production ortamında SQLite olamaz.")

    if not default_timezone:
        errors.append("MISSIO_DEFAULT_TIMEZONE production ortamında boş olamaz.")

    if cors_allowed_origins:
        insecure_origins = [
            origin.strip()
            for origin in cors_allowed_origins.split(",")
            if origin.strip().lower().startswith("http://")
        ]

        if insecure_origins:
            errors.append(
                "MISSIO_CORS_ALLOWED_ORIGINS production ortamında http:// içeremez; https:// kullanılmalıdır."
            )

    if errors:
        message = "Production ayarları güvenli değil:"
        details = "\n".join(f"- {error}" for error in errors)
        raise RuntimeError(f"{message}\n{details}")

