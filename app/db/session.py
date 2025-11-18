from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from app.core.config import settings

engine = None
_sessionmaker = None


def _ensure_engine_and_sessionmaker():

    ''' Ensure that the async engine and sessionmaker are created '''

    global engine, _sessionmaker

    if _sessionmaker is None:

        # Import inside function to avoid import-time dependency on asyncpg
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_async_engine(
            settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1),
            echo=getattr(settings, "DB_ECHO", False),
            future=True,
        )

        _sessionmaker = sessionmaker(
            engine,
            class_ = AsyncSession,
            autocommit = False,
            autoflush = False,
            expire_on_commit = False,
        )


def AsyncSessionLocal() -> AsyncSession:

    """ Factory function compatible with previous usage. Call to obtain a new AsyncSession """

    _ensure_engine_and_sessionmaker()

    return _sessionmaker()


def get_engine():
    
    """ Return the async engine, creating it if necessary """

    _ensure_engine_and_sessionmaker()
    return engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:

    """ Provides an async database session """

    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()