from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdateInDB


class IRoleRepository(ABC):
    @abstractmethod
    async def create(self, db: AsyncSession, role: RoleCreate) -> Role:
        """Create a new role. """
        pass

    @abstractmethod
    async def read_by_id(self, db: AsyncSession, role_id: UUID) -> Optional[Role]:
        """Get a role by its ID. """
        pass

    @abstractmethod
    async def read_with_filters(
        self, 
        db: AsyncSession,
        name: Optional[str] = None, 
        description: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Role]:
        """Get roles with filters. """
        pass

    @abstractmethod
    async def read_by_names(self, db: AsyncSession, names: List[str]) -> List[Role]:
        """Retrieve roles matching the provided list of names. """
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, role_id: UUID, update_data: RoleUpdateInDB) -> Role:
        """Update a role by its ID. """
        pass

    @abstractmethod
    async def assign_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> Role:
        """Add a permission to a role. """
        pass

    @abstractmethod
    async def assign_list_permissions(self, db: AsyncSession, role_id: UUID, permission_ids: List[UUID]) -> Role:
        """Assign a list of permissions to a role. """
        pass

    @abstractmethod
    async def remove_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> Role:
        """Remove a permission from a role. """
        pass

    @abstractmethod
    async def has_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> bool:
        """Return True if the role already has the given permission association. """
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, role_id: UUID) -> None:
        """Delete a role by its ID. """
        pass
