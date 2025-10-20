from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator

engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1),
    echo = True,
    future = True
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_ = AsyncSession,
    autocommit = False,
    autoflush = False,
    expire_on_commit = False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()