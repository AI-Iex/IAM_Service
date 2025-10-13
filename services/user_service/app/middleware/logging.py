import time
import uuid
import logging
import contextvars
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("nebulaops.user_service")

# Context var to hold request id per async context
_request_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def set_request_id(request_id: str) -> None:
   # Set the request_id in the context variable for the current context
    _request_id_ctx_var.set(request_id)


class RequestIdFilter(logging.Filter):
    # Logging filter that injects request_id from contextvar into log records
    def filter(self, record):
        record.request_id = _request_id_ctx_var.get()
        return True

class AccessLogMiddleware(BaseHTTPMiddleware):

    # Middleware that logs access details and manages request IDs
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_id(request_id)
        start = time.time()

        # Execute downstream; let exceptions propagate upwards
        try:
            response: Response = await call_next(request)
        except Exception:
            raise

        # Successful response path:
        duration_ms = (time.time() - start) * 1000
        user_id = getattr(request.state, "user_id", None)

        # Wrap logging
        try:
            logger.info(
                "access",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": getattr(response, "status_code", None),
                    "duration_ms": round(duration_ms, 2),
                    "user_id": user_id,
                },
            )
        except Exception as log_exc:
            fallback = logging.getLogger("nebulaops")
            fallback.exception("Failed to write access log: %s", log_exc)

        try:
            response.headers["X-Request-Id"] = request_id
        except Exception:
            
            # Defensive: If response.headers is read-only for some reason, ignore
            pass

        return response

__all__ = ["AccessLogMiddleware", "RequestIdFilter", "set_request_id"]
