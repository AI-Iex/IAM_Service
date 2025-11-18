from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.schemas.role import RoleCreate, RoleRead, RoleUpdate


class IRoleService(ABC):
    @abstractmethod
    async def create(self, role: RoleCreate) -> RoleRead:
        """Create a new role."""
        pass

    @abstractmethod
    async def read_by_id(self, role_id: UUID) -> RoleRead:
        """Get a role by its ID."""
        pass

    @abstractmethod
    async def read_with_filters(
        self, name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[RoleRead]:
        """Retrieve roles matching the provided filters with pagination."""
        pass

    @abstractmethod
    async def update(self, role_id: UUID, role: RoleUpdate) -> RoleRead:
        """Update a role by its ID."""
        pass

    @abstractmethod
    async def assign_permission(self, role_id: UUID, permission_id: UUID) -> RoleRead:
        """Assign a permission to a role."""
        pass

    @abstractmethod
    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> RoleRead:
        """Remove a permission from a role."""
        pass

    @abstractmethod
    async def delete(self, role_id: UUID) -> None:
        """Delete a role by its ID."""
        pass
