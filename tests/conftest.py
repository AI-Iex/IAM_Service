import asyncio
import logging
from typing import AsyncGenerator, Callable, Dict
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# During test runs we avoid writing to captured/closed streams by attaching
# a NullHandler to noisy loggers created by the app's logging config.
logging.getLogger("user_service").addHandler(logging.NullHandler())
logging.getLogger("access").addHandler(logging.NullHandler())
logging.getLogger("httpx").addHandler(logging.NullHandler())


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Return the AnyIO backend to use for tests (asyncio).
    """

    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create and yield an event loop instance for the whole test session.
    """

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """
    Create a dedicated async SQLAlchemy ``AsyncEngine`` for tests.
    - Uses ``settings.TEST_DATABASE_URL`` (required) and converts it to the async driver form.
    - Patches ``app.db.session`` to use this engine and a test sessionmaker.
    - Creates all tables before the test session and drops them afterwards.
    """

    test_url = getattr(settings, "TEST_DATABASE_URL", None)
    if not test_url:
        raise RuntimeError("TEST_DATABASE_URL must be set for tests")

    # If URL is a sync Postgres URL, convert it to asyncpg;
    # otherwise assume it's already an async-compatible URL.
    if test_url.startswith("postgresql://"):
        db_url = test_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        db_url = test_url
    engine = create_async_engine(
        db_url,
        echo=getattr(settings, "DB_ECHO", False),
        future=True,
    )

    # Patch app.db.session to use this engine and sessionmaker during tests.
    import app.db.session as app_db_session
    from sqlalchemy.orm import sessionmaker as sa_sessionmaker

    app_db_session.engine = engine
    app_db_session._sessionmaker = sa_sessionmaker(
        engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    # Provide AsyncSessionLocal factory compatible with the module's API
    app_db_session.AsyncSessionLocal = lambda: app_db_session._sessionmaker()

    # Create schema within the active event loop
    async with engine.begin() as conn:
        # Ensure all model modules are imported so metadata is complete
        import app.models.user  # noqa: F401
        import app.models.role  # noqa: F401
        import app.models.user_role  # noqa: F401
        import app.models.client  # noqa: F401
        import app.models.client_permission  # noqa: F401
        import app.models.permission  # noqa: F401
        import app.models.role_permission  # noqa: F401
        import app.models.refresh_token  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        # Drop schema and dispose engine in the active event loop
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional DB session per test function.

    The fixture:
    - Opens a connection and begins an outer transaction.
    - Yields an ``AsyncSession`` bound to that connection.
    - Rolls back any active transaction and the outer transaction afterwards so every test sees a clean database.
    """

    async with engine.connect() as conn:
        trans = await conn.begin()

        AsyncSessionTest = sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with AsyncSessionTest() as session:
            try:
                yield session
            finally:
                try:
                    if session is not None and session.in_transaction():
                        await session.rollback()
                except Exception:
                    # Avoid masking test failures with rollback issues
                    pass

                await session.close()
                # Roll back the outer transaction to undo all test changes
                await trans.rollback()


@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an ``AsyncClient`` bound to the FastAPI app using the test DB.

    - Overrides ``get_db`` so all requests use the ``db_session`` fixture.
    - Overrides auth dependency resolvers so they also use ``db_session`` when loading the current principal.
    """

    from app.main import app
    from app.db.session import get_db

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Override the DB dependency in the app
    app.dependency_overrides[get_db] = override_get_db

    # Also override principal resolvers so they use the test session (db_session)
    from app.dependencies import auth as auth_deps
    from app.core.security import AccessTokenType, decode_token
    from app.repositories.user import UserRepository
    from uuid import UUID as _UUID
    from fastapi import Depends, HTTPException, status

    async def _override_get_current_principal(
        token: str = Depends(auth_deps.oauth2_scheme),
    ):
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing token",
            )

        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # User tokens
        if getattr(payload, "type", None) == AccessTokenType.USER.value:
            user = await UserRepository().read_by_id(db_session, _UUID(payload.sub))
            from app.schemas.auth import Principal

            return Principal(
                kind=AccessTokenType.USER.value,
                token=payload,
                user=user,
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown token type",
        )

    # Optional principal returns None rather than raising
    async def _override_get_current_principal_optional(
        token: str = Depends(auth_deps.oauth2_scheme),
    ):
        try:
            return await _override_get_current_principal(token)
        except Exception:
            return None

    app.dependency_overrides[auth_deps.get_current_principal] = _override_get_current_principal
    app.dependency_overrides[auth_deps.get_current_principal_optional] = _override_get_current_principal_optional

    # Create the AsyncClient with ASGI transport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    # Cleanup overrides when the client is closed
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def token_headers(async_client: AsyncClient, db_session) -> Callable[[str, str], Dict[str, str]]:
    """
    Return a helper that produces Authorization headers for a given user.
    """

    from app.repositories.user import UserRepository
    from app.core.security import create_user_access_token

    async def _get(email: str, password: str) -> Dict[str, str]:
        # Read the user directly from the test session and create a JWT
        repo = UserRepository()
        user = await repo.read_by_email(db_session, email)
        if not user:
            raise RuntimeError("User not found when creating token headers")

        # Build permissions set from roles
        user_permissions = {
            perm.name for role in getattr(user, "roles", []) for perm in getattr(role, "permissions", [])
        }

        token_info = create_user_access_token(
            subject=str(user.id),
            permissions=list(user_permissions),
            is_superuser=user.is_superuser,
            require_password_change=user.require_password_change,
        )
        return {"Authorization": f"Bearer {token_info.access_token}"}

    return _get


@pytest.fixture
async def create_user(db_session) -> Callable[..., Dict]:
    """
    Convenience factory to create users directly in the test DB.
    """

    from app.repositories.user import UserRepository
    from app.schemas.user import UserCreateInDB
    from app.core.security import hash_password

    user_repo = UserRepository()

    async def _create(email: str, password: str, full_name: str = "Test User"):
        dto = UserCreateInDB(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=False,
            require_password_change=False,
        )
        user = await user_repo.create(db_session, dto)
        return user

    return _create
