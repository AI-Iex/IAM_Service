import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.user import router as users_router
from app.core.exceptions import DomainError, RepositoryError
from app.core.logging import setup_logging
from app.middleware.logging import AccessLogMiddleware
from app.db.base import init_db
from app.db.session import engine

# Setup logging early
setup_logging()
logger = logging.getLogger("nebulaops.user_service")

app = FastAPI(title="NebulaOps - User Service")

# Add middleware that logs access and sets request_id
app.add_middleware(AccessLogMiddleware)

@app.on_event("startup")
def startup_event():
    # DB initialization, will use migrations in production ** to change in future **
    init_db(engine)
    logger.info("startup complete")

# Include routers
app.include_router(users_router, prefix="/user_service")

# Domain exception handlers
@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(RepositoryError)
async def handle_repo_error(request: Request, exc: RepositoryError):
    logger.exception("Repository error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Database error"})

# Fallback middleware: catches any unhandled exceptions
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
