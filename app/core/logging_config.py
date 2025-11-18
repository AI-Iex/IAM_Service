import logging
import json
import sys
from typing import Optional
from datetime import datetime, timezone
from app.core.config import settings
from contextvars import ContextVar
from uuid import UUID

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id_ctx: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)


# region Privacy Masking Methods


def _mask_value(value: str, level: str) -> str:
    """Mask values depending on privacy level"""

    if level == "none":
        return value

    if isinstance(value, str):
        if "@" in value:
            return _mask_email(value)

        if level == "strict" and len(value) > 4:

            if len(value) >= 8 and all(c in "0123456789abcdef-" for c in value.lower()):
                return _mask_uuid(value)

            # If we want to mask everything
            # return "*" * (len(value) - 4) + value[-4:]

    return value


def _mask_email(email: str) -> str:
    """Mask email addresses for log safety"""

    try:
        local, domain = email.split("@", 1)
        if len(local) <= 1:
            masked_local = "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 1)
        domain_parts = domain.split(".")
        masked_domain = domain_parts[0][0] + "*" * (max(0, len(domain_parts[0]) - 1))
        if len(domain_parts) > 1:
            masked_domain = masked_domain + "." + ".".join(domain_parts[1:])
        return f"{masked_local}@{masked_domain}"
    except Exception:
        return "****"


def _mask_uuid(value: str) -> str:
    """Mask UUIDs like ids or jti for log safety"""

    try:
        if isinstance(value, str) and len(value) >= 8:
            return value[:8] + "..."
        return value
    except Exception:
        return "****"


# endregion Privacy Masking Methods


class JSONFormatter(logging.Formatter):
    """Build JSON log records with structured data and context info"""

    def __init__(self, privacy_level: Optional[str] = None):
        super().__init__()
        # Use provided privacy level or fallback to configured setting
        self.privacy_level = privacy_level or settings.LOG_PRIVACY_LEVEL

    def format(self, record: logging.LogRecord) -> str:
        """'Format log record as JSON string with context info and privacy masking"""

        # Basic log info
        log_dt = datetime.fromtimestamp(record.created, tz=timezone.utc)

        # The main payload of the log record
        payload = {
            "timestamp": log_dt.isoformat().replace("+00:00", "Z"),  # ISO 8601 UTC timestamp
            "level": record.levelname,  # Log level name (e.g., INFO, ERROR)
            "logger": record.name,  # Logger name (e.g., "user_service")
            "function": record.funcName,  # Function name where log was called
            "message": record.getMessage(),  # The log message
        }

        # Keys we never want to copy into "extra" (avoid duplication / noise)
        blacklist = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "taskName",
        }

        # Build extras from known attributes that were explicitly set via logger.extra
        extras = {}
        for k, v in record.__dict__.items():
            if k in blacklist:
                continue
            # avoid duplicating logger name inside extras
            if k == "name":
                continue
            # skip None values to reduce noise
            if v is None:
                continue
            # If someone added very large objects, convert to str
            try:
                json.dumps(v, default=str)
                extras[k] = v
            except Exception:
                extras[k] = str(v)

        if extras:
            payload["extra"] = extras

        # Apply privacy masking to sensitive data in payload using the formatter's
        # configured privacy level. This allows tests to instantiate the
        # formatter with different privacy levels for verification.
        def _mask_sensitive_data(obj, level: str):
            if level == "none":
                return obj
            if isinstance(obj, dict):
                return {k: _mask_sensitive_data(v, level) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_mask_sensitive_data(v, level) for v in obj]
            elif isinstance(obj, str):
                return _mask_value(obj, level)
            return obj

        payload = _mask_sensitive_data(payload, self.privacy_level)

        return json.dumps(payload, default=str)


def setup_logging(
    service_name: str = settings.SERVICE_NAME, level: int = logging.INFO, privacy_level: Optional[str] = None
) -> logging.Logger:
    """Setup root logger with JSON formatter and context filters"""

    # Create console handler with JSON formatter
    handler = logging.StreamHandler(stream=sys.stdout)
    # Set handler level
    handler.setLevel(level)
    # Set JSON formatter
    handler.setFormatter(JSONFormatter(privacy_level=privacy_level))

    class RequestIdFilter(logging.Filter):
        """Class to add request_id and request_by_user_id from contextvars to log records"""

        def filter(self, record: logging.LogRecord) -> bool:
            """Add request_id and request_by_user_id to log record if available"""

            try:
                rid = _request_id_ctx.get(None)
                if rid is not None:
                    record.request_id = rid
            except Exception:
                record.request_id = None
            try:
                uid = _user_id_ctx.get(None)
                if uid is not None:
                    # attach as request_by_user_id to avoid legacy 'user_id' key
                    record.request_by_user_id = str(uid)
            except Exception:
                record.request_by_user_id = None

            return True

    # Attach the filter to the handler
    handler.addFilter(RequestIdFilter())

    # Configure root logger
    root = logging.getLogger()
    # Clear existing handlers and add our handler to avoid duplicate logs
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(level)

    return logging.getLogger(service_name)


def configure_third_party_loggers(level: int = logging.WARNING, attach_json_handler: bool = True):
    """Configure logging for common third-party libraries used in FastAPI apps"""

    # List of common third-party loggers to configure
    third_party = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "asyncio",
        "urllib3",
    ]

    handler = None

    if attach_json_handler:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(JSONFormatter())
    for name in third_party:
        lg = logging.getLogger(name)
        lg.setLevel(level)
        if attach_json_handler:
            lg.handlers = [handler]
            lg.propagate = False
        else:
            lg.propagate = False


# region ContextVar Management Methods (Request ID and User ID)


def get_request_context():
    """Get current request_id and user_id from contextvars."""

    return _request_id_ctx.get(None), _user_id_ctx.get(None)


def set_request_context(request_id: str, user_id: Optional[UUID] = None):
    """
    Set request_id and optionally user_id in contextvars.
    Returns a tuple of tokens (request_token, user_token) that can be used to reset context.
    """

    request_token = _request_id_ctx.set(request_id)
    user_token = None

    if user_id is not None:
        user_token = _user_id_ctx.set(user_id)

    return request_token, user_token


def reset_request_context(request_token, user_token=None):
    """Reset request_id and user_id in contextvars using provided tokens"""

    if request_token is not None:
        _request_id_ctx.reset(request_token)
    if user_token is not None:
        _user_id_ctx.reset(user_token)


# endregion ContextVar Management Methods (Request ID and User ID)
