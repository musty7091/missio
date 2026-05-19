from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import clear_rate_limit_state
from app.main import app


def main() -> None:
    """Run rate limit smoke checks."""

    original_enabled = settings.rate_limit_enabled
    original_max_requests = settings.rate_limit_max_requests
    original_window_seconds = settings.rate_limit_window_seconds

    settings.rate_limit_enabled = True
    settings.rate_limit_max_requests = 2
    settings.rate_limit_window_seconds = 60
    clear_rate_limit_state()

    client = TestClient(app)
    headers = {"x-forwarded-for": "203.0.113.10"}

    try:
        first_response = client.get("/api/v1/auth/me", headers=headers)
        second_response = client.get("/api/v1/auth/me", headers=headers)
        third_response = client.get("/api/v1/auth/me", headers=headers)

        if first_response.status_code != 401:
            raise RuntimeError("İlk istek auth nedeniyle 401 dönmeliydi.")

        if second_response.status_code != 401:
            raise RuntimeError("İkinci istek auth nedeniyle 401 dönmeliydi.")

        if third_response.status_code != 429:
            raise RuntimeError("Üçüncü istek rate limit nedeniyle 429 dönmeliydi.")

        if third_response.headers.get("retry-after") is None:
            raise RuntimeError("Rate limit response Retry-After header içermiyor.")

        print("Rate limit bloklama kontrolü başarılı.")
        print("Retry-After header kontrolü başarılı.")
        print("Rate limit güvenlik temel kontrolü başarılı.")
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_max_requests = original_max_requests
        settings.rate_limit_window_seconds = original_window_seconds
        clear_rate_limit_state()


if __name__ == "__main__":
    main()
