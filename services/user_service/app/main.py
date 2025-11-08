import logging
from fastapi import FastAPI
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
from app.middleware.exception_handler import exception_handling_middleware
from app.db.base import init_db
from app.db.session import get_engine
from app.core.config import settings
from app.core.logging_config import setup_logging, configure_third_party_loggers
from app.core.permissions_loader import Permissions


logger = setup_logging()
configure_third_party_loggers(level = logging.WARNING, attach_json_handler = False)


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description=settings.SERVICE_DESCRIPTION,
    license_info={"name": settings.SERVICE_LICENSE},
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register middlewares so that the access-log middleware is the outermost wrapper.
app.middleware("http")(access_log_middleware)
app.middleware("http")(exception_handling_middleware)
app.middleware("http")(auth_context_middleware)
app.middleware("http")(context_middleware)

@app.on_event("startup")
async def startup_event():
    # Ensure engine exists and run DB initialization (creates tables if needed)
    engine = get_engine()
    await init_db(engine)
    logger.info("Service started successfully")

# Include routers
app.include_router(health_router, prefix = settings.route_prefix)
app.include_router(auth_router, prefix = settings.route_prefix)
app.include_router(client_router, prefix = settings.route_prefix)
app.include_router(users_router, prefix = settings.route_prefix)
app.include_router(role_router, prefix = settings.route_prefix)
app.include_router(permission_router, prefix = settings.route_prefix)