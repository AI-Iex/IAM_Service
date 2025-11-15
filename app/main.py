import logging
from fastapi import FastAPI
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
from app.middleware.exception_handler import (
    exception_handling_middleware,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from app.db.base import init_db
from app.db.bootstrap import create_default_superuser, seed_permissions_and_roles
from app.db.session import get_engine
from app.core.config import settings
from app.core.logging_config import setup_logging, configure_third_party_loggers
from app.core.permissions_loader import Permissions


logger = setup_logging()
configure_third_party_loggers(level = logging.WARNING, attach_json_handler = False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    try:
        await init_db(engine)
        logger.info("Database initialized successfully")
        # Seed base permissions and roles first (idempotent)
        await seed_permissions_and_roles(engine)
        logger.info("Permissions and default roles seeded")

        if settings.CREATE_SUPERUSER_ON_STARTUP:
            await create_default_superuser(engine)
            logger.info("Default superuser created on startup")

        yield
    finally:
        engine = get_engine()
        await engine.dispose()
        logger.info("Database connections closed")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description=settings.SERVICE_DESCRIPTION,
    license_info={"name": settings.SERVICE_LICENSE},
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Register middlewares so that the access-log middleware is the outermost wrapper.
app.middleware("http")(access_log_middleware)
app.middleware("http")(exception_handling_middleware)
app.middleware("http")(auth_context_middleware)
app.middleware("http")(context_middleware)

# Register a FastAPI exception handler so that validation errors raised during
# routing (before middleware) are normalized to the same error payload used
# by the middleware.
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

# Lifespan handler registered above handles startup and shutdown work.

# Include routers
app.include_router(health_router, prefix = settings.route_prefix)
app.include_router(auth_router, prefix = settings.route_prefix)
app.include_router(client_router, prefix = settings.route_prefix)
app.include_router(users_router, prefix = settings.route_prefix)
app.include_router(role_router, prefix = settings.route_prefix)
app.include_router(permission_router, prefix = settings.route_prefix)