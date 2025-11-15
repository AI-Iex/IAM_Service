from abc import ABC, abstractmethod
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession


class IUnitOfWork(ABC):
    
    @abstractmethod
    async def __aenter__(self) -> AsyncSession:
        """Enter the context and return the session."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context, handling commit/rollback."""
        pass
