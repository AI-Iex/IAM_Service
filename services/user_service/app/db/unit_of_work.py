from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, AsyncContextManager
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

UnitOfWorkFactory = Callable[[], AsyncContextManager[AsyncSession]]

@asynccontextmanager
async def async_unit_of_work() -> AsyncIterator[AsyncSession]:
    db = AsyncSessionLocal()
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()