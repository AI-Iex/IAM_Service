from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate, ClientCreateResponse


class IClientService(ABC):

    @abstractmethod
    async def create(self, payload: ClientCreate) -> ClientCreateResponse:
        """Create a new client."""
        pass

    @abstractmethod
    async def read_by_id(self, client_id: UUID) -> ClientRead:
        """Retrieve a client by its ID."""
        pass

    @abstractmethod
    async def read_with_filters(
        self, name: Optional[str] = None, is_active: Optional[bool] = None, skip: int = 0, limit: int = 100
    ) -> List[ClientRead]:
        """Retrieve clients matching the provided filters with pagination."""
        pass

    @abstractmethod
    async def update(self, client_id: UUID, payload: ClientUpdate) -> ClientRead:
        """Update a client by its ID."""
        pass

    @abstractmethod
    async def assign_permission(self, client_id: UUID, permission_id: UUID) -> ClientRead:
        """Assign a permission to a client by ID."""
        pass

    @abstractmethod
    async def remove_permission(self, client_id: UUID, permission_id: UUID) -> ClientRead:
        """Remove a permission from a client."""
        pass

    @abstractmethod
    async def delete(self, client_id: UUID) -> None:
        """Delete a client by its ID."""
        pass
