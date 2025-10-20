from fastapi.routing import APIRoute
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import EntityAlreadyExists, DomainError, RepositoryError, NotFoundError
import logging

logger = logging.getLogger("nebulaops.user_service")

class ExceptionHandlingRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def custom_route_handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError as exc:
                
                first_error = exc.errors()[0] if exc.errors() else {}
                
                if first_error.get("type") == "uuid_parsing":
                    return JSONResponse(
                        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT,
                        content={
                            "error": "INVALID_UUID_FORMAT",
                            "message": "The provided ID is not a valid UUID format",
                            "details": "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                        }
                    )
                else:
                    return JSONResponse(
                        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT,
                        content={
                            "error": "VALIDATION_ERROR", 
                            "message": "Request validation failed",
                            "details": exc.errors()
                        }
                    )
            except EntityAlreadyExists as exc:
                return JSONResponse(status_code = status.HTTP_409_CONFLICT, content={"detail": str(exc)})
            except DomainError as exc:
                return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})
            except NotFoundError as exc:
                return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})
            except RepositoryError as exc:
                logger.exception("Repository error in route: %s", exc)
                return JSONResponse(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Database error"})
            except Exception as exc:
                logger.exception("Unhandled exception in route: %s", exc)
                return JSONResponse(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})
        return custom_route_handler