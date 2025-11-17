import logging
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.user import router as users_router
from app.api.routes.auth import router as auth_router
from app.api.routes.role import router as role_router
from app.api.routes.health import router as health_router
from app.api.routes.permission import router as permission_router
from app.api.routes.client import router as client_router
from app.middleware.logging import access_log_middleware
from app.middleware.context import context_middleware
from app.middleware.auth_context import auth_context_middleware
from app.middleware.exception_handler import exception_handling_middleware, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from app.db.session import get_engine
from app.core.config import settings
from app.core.logging_config import setup_logging, configure_third_party_loggers
from app.core.permissions_loader import Permissions

logger = setup_logging()
configure_third_party_loggers(level = logging.WARNING, attach_json_handler = False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    """Lifespan handler.

    NOTE: Database schema creation and seeding are expected to be performed by an external migration step.
    """

    engine = get_engine()
    try:
        yield
    finally:
        engine = get_engine()
        await engine.dispose()
        logger.info("Database connections closed")

app = FastAPI(
    title = settings.SERVICE_NAME,
    version = settings.SERVICE_VERSION,
    description = settings.SERVICE_DESCRIPTION,
    license_info = {"name": settings.SERVICE_LICENSE},
    docs_url = "/docs",
    redoc_url = "/redoc",
    lifespan = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.CORS_ORIGINS,
    allow_credentials = True,
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers = ["Authorization", "Content-Type", "X-Requested-With"],
)

# Register middlewares.
app.middleware("http")(access_log_middleware)
app.middleware("http")(exception_handling_middleware)
app.middleware("http")(auth_context_middleware)
app.middleware("http")(context_middleware)

# Register a FastAPI exception handler.
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

# Root endpoint - redirect to documentation
@app.get("/", include_in_schema = False)
async def root():

    """Redirect root to API documentation"""
    
    return RedirectResponse(url="/docs")

# Include routers
app.include_router(health_router, prefix = settings.route_prefix)
app.include_router(auth_router, prefix = settings.route_prefix)
app.include_router(client_router, prefix = settings.route_prefix)
app.include_router(users_router, prefix = settings.route_prefix)
app.include_router(role_router, prefix = settings.route_prefix)
app.include_router(permission_router, prefix = settings.route_prefix)