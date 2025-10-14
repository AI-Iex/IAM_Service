from fastapi.routing import APIRoute
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import EntityAlreadyExists, DomainError, RepositoryError, NotFoundError
import logging

logger = logging.getLogger("nebulaops.user_service")

class ExceptionHandlingRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def custom_route_handler(request: Request):
            try:
                return await original(request)
            except EntityAlreadyExists as exc:
                return JSONResponse(status_code=409, content={"detail": str(exc)})
            except DomainError as exc:
                return JSONResponse(status_code=400, content={"detail": str(exc)})
            except NotFoundError as exc:
                return JSONResponse(status_code=404, content={"detail": str(exc)})
            except RepositoryError as exc:
                logger.exception("Repository error in route: %s", exc)
                return JSONResponse(status_code=500, content={"detail": "Database error"})
            except Exception as exc:
                logger.exception("Unhandled exception in route: %s", exc)
                return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        return custom_route_handler
