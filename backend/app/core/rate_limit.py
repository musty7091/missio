from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from threading import Lock

from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


RATE_LIMIT_STATE: dict[str, deque[float]] = defaultdict(deque)
RATE_LIMIT_LOCK = Lock()

EXEMPT_PATHS = {
    "/",
    "/api/v1/health",
}


def clear_rate_limit_state() -> None:
    """Clear in-memory rate limit state."""

    with RATE_LIMIT_LOCK:
        RATE_LIMIT_STATE.clear()


def get_client_identifier(request: Request) -> str:
    """Return best-effort client identifier."""

    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()

        if first_ip:
            return first_ip[:100]

    if request.client is not None and request.client.host:
        return request.client.host[:100]

    return "unknown"


def get_rate_limit_key(request: Request) -> str:
    """Build rate limit key from client and request path."""

    client_identifier = get_client_identifier(request)
    path = request.url.path

    return f"{client_identifier}:{path}"


def should_skip_rate_limit(request: Request) -> bool:
    """Return whether request should bypass rate limiting."""

    if not settings.rate_limit_enabled:
        return True

    if request.url.path in EXEMPT_PATHS:
        return True

    return False


def prune_old_requests(
    request_times: deque[float],
    *,
    now: float,
    window_seconds: int,
) -> None:
    """Remove request timestamps outside the rate limit window."""

    cutoff = now - window_seconds

    while request_times and request_times[0] <= cutoff:
        request_times.popleft()


def build_rate_limit_response(retry_after_seconds: int) -> JSONResponse:
    """Build safe rate limit response."""

    response = JSONResponse(
        status_code=429,
        content={
            "detail": "Çok fazla istek gönderildi. Lütfen daha sonra tekrar deneyin.",
        },
    )
    response.headers["Retry-After"] = str(max(retry_after_seconds, 1))
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_max_requests)
    response.headers["X-RateLimit-Remaining"] = "0"

    return response


async def add_rate_limit(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Apply simple in-memory rate limiting."""

    if should_skip_rate_limit(request):
        return await call_next(request)

    now = time.monotonic()
    key = get_rate_limit_key(request)
    max_requests = settings.rate_limit_max_requests
    window_seconds = settings.rate_limit_window_seconds

    if max_requests <= 0 or window_seconds <= 0:
        return await call_next(request)

    with RATE_LIMIT_LOCK:
        request_times = RATE_LIMIT_STATE[key]
        prune_old_requests(
            request_times,
            now=now,
            window_seconds=window_seconds,
        )

        if len(request_times) >= max_requests:
            oldest_request = request_times[0]
            retry_after = int((oldest_request + window_seconds) - now) + 1

            return build_rate_limit_response(retry_after)

        request_times.append(now)
        remaining = max(max_requests - len(request_times), 0)

    response = await call_next(request)
    response.headers.setdefault("X-RateLimit-Limit", str(max_requests))
    response.headers.setdefault("X-RateLimit-Remaining", str(remaining))

    return response
