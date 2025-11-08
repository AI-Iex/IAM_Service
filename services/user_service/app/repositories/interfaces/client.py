from abc import ABC, abstractmethod
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.client import Client
from app.schemas.client import ClientCreateInDB, ClientUpdate
from uuid import UUID


class IClientRepository(ABC):

    @abstractmethod
    async def create(self, db: AsyncSession, client: ClientCreateInDB) -> Client:
        ''' Create and persist a Client row returning the created object '''
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, client_id: UUID, update_data: ClientUpdate) -> Client:
        ''' Update and persist a Client row returning the updated object '''
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, client_id: UUID) -> None:
        ''' Delete a Client by its ID '''
        pass

    @abstractmethod
    async def read_by_id(self, db: AsyncSession, client_id: UUID) -> Optional[Client]:
        ''' Retrieve a client by its ID '''
        pass

    @abstractmethod
    async def read_by_clientid(self, db: AsyncSession, clientid: UUID) -> Optional[Client]:
        ''' Retrieve a client by its client ID used for authentication '''
        pass

    @abstractmethod
    async def read_with_filters(self, db: AsyncSession, name: Optional[str] = None, is_active: Optional[bool] = None, skip: int = 0, limit: int = 100) -> List[Client]:
        ''' Get clients with filters '''
        pass

    @abstractmethod
    async def set_permissions(self, db: AsyncSession, client_id: UUID, permission_ids: List[UUID]) -> Client:
        ''' Assign permissions to a client '''
        pass

    @abstractmethod
    async def add_permission(self, db: AsyncSession, client_id: UUID, permission_id: UUID) -> Client:
        ''' Add a permission to a client '''
        pass

    @abstractmethod
    async def remove_permission(self, db: AsyncSession, client_id: UUID, permission_ids: UUID) -> Client:
        ''' Delete permissions from a client '''
        pass

    @abstractmethod
    async def has_permission(self, db: AsyncSession, client_id: UUID, permission_id: UUID) -> bool:
        """Return True if the client already has the given permission association."""
        pass