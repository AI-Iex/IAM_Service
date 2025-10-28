from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import EntityAlreadyExists, DomainError, RepositoryError, NotFoundError
import logging
import traceback
import re
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger("user_service")

# Determine project root for path sanitization
try:
    _PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
except Exception:
    _PROJECT_ROOT = None


def _sanitize_traceback(tb: str, max_lines: int = 25) -> str:

    '''Sanitize traceback by redacting absolute paths and limiting number of lines'''

    if not tb:
        return ""
    
    # Redact project root paths
    if _PROJECT_ROOT:
        tb = tb.replace(_PROJECT_ROOT, "[REDACTED_PATH]")

    # Redact user home directories
    tb = re.sub(r"[A-Za-z]:\\\\Users\\\\[^\\\\\n]+", "[REDACTED_USER]", tb)
    tb = re.sub(r"/home/[^/\n]+", "[REDACTED_USER]", tb)
    lines = tb.strip().splitlines()
    if len(lines) > max_lines:
        head = lines[:10]
        tail = lines[-10:]
        return "\n".join(head + ["...omitted..."] + tail)
    return "\n".join(lines)

# Mapping of error types to error codes and HTTP status codes
ERROR_MAP = {
    "validation": {"code": "APP.VAL.001", "http": status.HTTP_422_UNPROCESSABLE_ENTITY},
    "invalid_uuid": {"code": "APP.VAL.002", "http": status.HTTP_422_UNPROCESSABLE_ENTITY},
    "user_exists": {"code": "APP.USR.001", "http": status.HTTP_409_CONFLICT},
    "domain_error": {"code": "APP.BIZ.001", "http": status.HTTP_400_BAD_REQUEST},
    "not_found": {"code": "APP.ERR.404", "http": status.HTTP_404_NOT_FOUND},
    "db_error": {"code": "APP.DB.001", "http": status.HTTP_500_INTERNAL_SERVER_ERROR},
    "internal": {"code": "APP.ERR.500", "http": status.HTTP_500_INTERNAL_SERVER_ERROR},
}

def _make_error_response(request_id: str | None, error_code: str, error_type: str, message: str, details = None):
    body = {
        "request_id": request_id,
        "error_code": error_code,
        "error_type": error_type,
        "message": message,
    }
    if details is not None:
        body["details"] = details
    return body

async def exception_handling_middleware(request: Request, call_next):
    request_id = getattr(request.state, "request_id", None)

    try:
        response = await call_next(request)
        return response

    except RequestValidationError as exc:
        # Validation errors (422) - include details
        first_error = exc.errors()[0] if exc.errors() else {}
        if first_error.get("type") == "uuid_parsing":
            em = ERROR_MAP["invalid_uuid"]
            logger.warning(
                "Invalid UUID format in request",
                extra={
                    "request_id": request_id,
                    "error_code": em["code"],
                    "detail": first_error,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=em["http"],
                content=_make_error_response(
                    request_id=request_id,
                    error_code=em["code"],
                    error_type="INVALID_UUID_FORMAT",
                    message="The provided ID is not a valid UUID format",
                    details={"expected": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}
                ),
            )
        else:
            em = ERROR_MAP["validation"]
            logger.warning(
                "Request validation failed",
                extra={
                    "request_id": request_id,
                    "error_code": em["code"],
                    "errors": exc.errors(),
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=em["http"],
                content=_make_error_response(
                    request_id=request_id,
                    error_code=em["code"],
                    error_type="VALIDATION_ERROR",
                    message="Request validation failed",
                    details=exc.errors()
                ),
            )

    except EntityAlreadyExists as exc:
        em = ERROR_MAP["user_exists"]
        logger.warning(
            "Entity already exists",
            extra={
                "request_id": request_id,
                "error_code": em["code"],
                "detail": str(exc),
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=em["http"],
            content=_make_error_response(
                request_id=request_id,
                error_code=em["code"],
                error_type="ENTITY_ALREADY_EXISTS",
                message=str(exc)
            )
        )

    except DomainError as exc:
        em = ERROR_MAP["domain_error"]
        logger.warning(
            "Domain validation error",
            extra={
                "request_id": request_id,
                "error_code": em["code"],
                "detail": str(exc),
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=em["http"],
            content=_make_error_response(
                request_id=request_id,
                error_code=em["code"],
                error_type="DOMAIN_ERROR",
                message=str(exc)
            )
        )

    except NotFoundError as exc:
        em = ERROR_MAP["not_found"]
        logger.info(
            "Resource not found",
            extra={
                "request_id": request_id,
                "error_code": em["code"],
                "detail": str(exc),
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=em["http"],
            content=_make_error_response(
                request_id=request_id,
                error_code=em["code"],
                error_type="NOT_FOUND",
                message=str(exc)
            )
        )

    except RepositoryError as exc:
        em = ERROR_MAP["db_error"]
        # sanitized traceback for internal logs only (include full trace only in DEBUG)
        raw_tb = traceback.format_exc()
        sanitized_tb = _sanitize_traceback(raw_tb)
        log_extra = {
            "request_id": request_id,
            "error_code": em["code"],
            "detail": str(exc)[:500],
            "path": request.url.path,
            "method": request.method,
        }
        if getattr(settings, "DEBUG", False):
            log_extra["sanitized_traceback"] = sanitized_tb
        logger.error("Repository error while handling request (sanitized)", extra=log_extra)
        return JSONResponse(
            status_code=em["http"],
            content=_make_error_response(
                request_id=request_id,
                error_code=em["code"],
                error_type="REPOSITORY_ERROR",
                message="Database error"
            )
        )

    except Exception as exc:
        em = ERROR_MAP["internal"]
        raw_tb = traceback.format_exc()
        sanitized_tb = _sanitize_traceback(raw_tb)
        log_extra = {
            "request_id": request_id,
            "error_code": em["code"],
            "detail": str(exc)[:500],
            "path": request.url.path,
            "method": request.method,
        }
        # include sanitized traceback only in DEBUG logs
        if getattr(settings, "DEBUG", False):
            log_extra["sanitized_traceback"] = sanitized_tb
        logger.error("Unhandled exception in route (sanitized)", extra=log_extra)
        return JSONResponse(
            status_code=em["http"],
            content=_make_error_response(
                request_id=request_id,
                error_code=em["code"],
                error_type="INTERNAL_SERVER_ERROR",
                message="Internal server error"
            )
        )