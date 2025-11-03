import time
import uuid
import logging
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import set_request_context, reset_request_context

logger = logging.getLogger("access")


async def access_log_middleware(request: Request, call_next):
    
    """Structured access log middleware.

    Responsibilities:
    - Ensure a request_id exists and set it on request.state
    - Populate contextvars with request_id so log filters can inject it
    - Measure request duration and log structured info (route, status, duration, client_ip, user_id)
    - Return X-Request-Id header for client correlation
    """
    start = time.perf_counter()

    # Ensure request_id (may be set by middleware); generate if missing
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    request.state.request_id = request_id

    # Set request context so RequestIdFilter can pick it up for all logs in this request
    request_token, user_token = set_request_context(request_id)

    try:
        response: Response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        # Determine an appropriate HTTP status code when possible.
        status_code = None
        try:
            if isinstance(exc, HTTPException):
                status_code = exc.status_code
            else:
                status_code = getattr(exc, "status_code", None)
        except Exception:
            status_code = None
        if status_code is None:
            status_code = 500

        # Minimal summary in access log: avoid full traceback and internal paths.
        logger.error(
            "HTTP request error (summary)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "route": getattr(request.scope.get("route"), "name", None),
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else None,
                # short summary only
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:200],
            },
        )
        # cleanup context before re-raising so outer exception handlers/middlewares can run
        try:
            reset_request_context(request_token, user_token)
        except Exception:
            pass
        raise

    # Compute duration and log
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "route": getattr(request.scope.get("route"), "name", None),
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": request.client.host if request.client else None,
            "request_by_user_id": getattr(request.state, "user_id", None),
        },
    )

    # Ensure header for correlation
    if isinstance(response, Response):
        response.headers.setdefault("X-Request-Id", request_id)

    # Cleanup context after logging
    try:
        reset_request_context(request_token, user_token)
    except Exception:
        pass

    return response