from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.client import Client


class IClientRepository(ABC):

    @abstractmethod
    async def get_by_client_id(self, db: AsyncSession, client_id: str) -> Optional[Client]:
        ''' Retrieve a client by its ID '''
        pass

    @abstractmethod
    async def create_client(self, db: AsyncSession, client_id: str, hashed_secret: str, name: str | None = None, scopes: str | None = None) -> Client:
        ''' Create and persist a Client row returning the created object '''
        pass
