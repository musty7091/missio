from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import clear_rate_limit_state
from app.main import app


def test_rate_limit_blocks_after_configured_limit() -> None:
    original_enabled = settings.rate_limit_enabled
    original_max_requests = settings.rate_limit_max_requests
    original_window_seconds = settings.rate_limit_window_seconds

    settings.rate_limit_enabled = True
    settings.rate_limit_max_requests = 2
    settings.rate_limit_window_seconds = 60
    clear_rate_limit_state()

    client = TestClient(app)
    headers = {"x-forwarded-for": "198.51.100.1"}

    try:
        first_response = client.get("/api/v1/auth/me", headers=headers)
        second_response = client.get("/api/v1/auth/me", headers=headers)
        third_response = client.get("/api/v1/auth/me", headers=headers)

        assert first_response.status_code == 401
        assert second_response.status_code == 401
        assert third_response.status_code == 429
        assert third_response.headers["retry-after"]
        assert third_response.headers["x-ratelimit-remaining"] == "0"
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_max_requests = original_max_requests
        settings.rate_limit_window_seconds = original_window_seconds
        clear_rate_limit_state()


def test_rate_limit_uses_client_ip_isolation() -> None:
    original_enabled = settings.rate_limit_enabled
    original_max_requests = settings.rate_limit_max_requests
    original_window_seconds = settings.rate_limit_window_seconds

    settings.rate_limit_enabled = True
    settings.rate_limit_max_requests = 1
    settings.rate_limit_window_seconds = 60
    clear_rate_limit_state()

    client = TestClient(app)

    try:
        first_client_response = client.get(
            "/api/v1/auth/me",
            headers={"x-forwarded-for": "198.51.100.2"},
        )
        second_client_response = client.get(
            "/api/v1/auth/me",
            headers={"x-forwarded-for": "198.51.100.3"},
        )

        assert first_client_response.status_code == 401
        assert second_client_response.status_code == 401
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_max_requests = original_max_requests
        settings.rate_limit_window_seconds = original_window_seconds
        clear_rate_limit_state()


def test_rate_limit_can_be_disabled() -> None:
    original_enabled = settings.rate_limit_enabled
    original_max_requests = settings.rate_limit_max_requests
    original_window_seconds = settings.rate_limit_window_seconds

    settings.rate_limit_enabled = False
    settings.rate_limit_max_requests = 1
    settings.rate_limit_window_seconds = 60
    clear_rate_limit_state()

    client = TestClient(app)
    headers = {"x-forwarded-for": "198.51.100.4"}

    try:
        first_response = client.get("/api/v1/auth/me", headers=headers)
        second_response = client.get("/api/v1/auth/me", headers=headers)

        assert first_response.status_code == 401
        assert second_response.status_code == 401
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_max_requests = original_max_requests
        settings.rate_limit_window_seconds = original_window_seconds
        clear_rate_limit_state()
