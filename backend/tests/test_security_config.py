from app.core.security_config import (
    is_secret_key_strong,
    validate_runtime_security_settings,
)


def test_secret_key_rejects_default_value() -> None:
    assert not is_secret_key_strong("change-this-secret-key-before-production")


def test_secret_key_rejects_short_value() -> None:
    assert not is_secret_key_strong("short")


def test_secret_key_accepts_strong_value() -> None:
    assert is_secret_key_strong(
        "Missio_Production_Secret_Key_2026_With_Strong_Length!"
    )


def test_production_debug_enabled_fails() -> None:
    report = validate_runtime_security_settings(
        environment="production",
        debug=True,
        secret_key="Missio_Production_Secret_Key_2026_With_Strong_Length!",
        database_url="sqlite:///C:/missio/data/missio.db",
        default_timezone="Europe/Istanbul",
    )

    assert report.has_failures
    assert any(
        result.name == "debug" and result.status == "FAIL"
        for result in report.results
    )


def test_production_default_secret_fails() -> None:
    report = validate_runtime_security_settings(
        environment="production",
        debug=False,
        secret_key="change-this-secret-key-before-production",
        database_url="sqlite:///C:/missio/data/missio.db",
        default_timezone="Europe/Istanbul",
    )

    assert report.has_failures
    assert any(
        result.name == "secret_key" and result.status == "FAIL"
        for result in report.results
    )


def test_local_default_secret_warns_but_does_not_fail() -> None:
    report = validate_runtime_security_settings(
        environment="local",
        debug=True,
        secret_key="change-this-secret-key-before-production",
        database_url="sqlite:///./missio_local.db",
        default_timezone="Europe/Istanbul",
    )

    assert not report.has_failures
    assert report.has_warnings
