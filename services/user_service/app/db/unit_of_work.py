from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.db.interfaces.unit_of_work import IUnitOfWork


class SQLAlchemyUnitOfWork(IUnitOfWork):

    def __init__(self):
        self._db: AsyncSession | None = None

    # Called when entering the async with block (async with self.uow_factory() as db)
    async def __aenter__(self) -> AsyncSession:

        ''' Enter the async context manager, creating a new AsyncSession '''

        self._db = AsyncSessionLocal()
        return self._db

    # Called when exiting the async with block
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:

        ''' Exit the async context manager, committing or rolling back as needed '''

        try:
            if exc_type:
                await self._db.rollback()
            else:
                await self._db.commit()
        finally:
            await self._db.close()

# Factory type for creating UnitOfWork instances
UnitOfWorkFactory = Callable[[], IUnitOfWork]

def get_uow_factory() -> UnitOfWorkFactory:
    return SQLAlchemyUnitOfWork