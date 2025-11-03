from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate


class IPermissionService(ABC):

    @abstractmethod
    async def create(self, payload: PermissionCreate) -> PermissionRead:
        """Create a new permission."""
        pass

    @abstractmethod
    async def read_with_filters(self, 
                                name: Optional[List[str]] = None, 
                                service_name: Optional[str] = None,
                                description: Optional[str] = None, 
                                skip: int = 0, 
                                limit: int = 100
                                ) -> List[PermissionRead]:
        """Get permissions with filters."""
        pass

    @abstractmethod
    async def read_by_id(self, permission_id: UUID) -> PermissionRead:
        """Get a permission by its ID."""
        pass

    @abstractmethod
    async def update(self, permission_id: UUID, payload: PermissionUpdate) -> PermissionRead:
        """Update a permission by its ID."""
        pass

    @abstractmethod
    async def delete(self, permission_id: UUID) -> None:
        """Delete a permission by its ID."""
        pass
