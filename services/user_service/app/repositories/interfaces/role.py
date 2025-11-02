from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate, RoleUpdateInDB
from typing import Optional, List


class IRoleRepository(ABC):
    @abstractmethod
    async def create(self, db: AsyncSession, role: RoleCreate) -> Role:
        """Create a new role."""
        pass

    @abstractmethod
    async def read_by_id(self, db: AsyncSession, role_id: UUID) -> Optional[Role]:
        """Get a role by its ID."""
        pass

    @abstractmethod
    async def read_with_filters(self, 
                                db: AsyncSession,
                                name: Optional[List[str]] = None, 
                                description: Optional[str] = None,
                                skip: int = 0, 
                                limit: int = 100
                            ) -> List[Role]:
        """Get roles with filters."""
        pass

    @abstractmethod
    async def read_by_names(self, db: AsyncSession, names: List[str]) -> List[Role]:
        """Retrieve roles matching the provided list of names."""
        pass

    @abstractmethod
    async def read_by_user_id_with_permissions(self, db: AsyncSession, user_id: UUID) -> List[Role]:
        """Retrieve roles assigned to a user including their permissions."""
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, role_id: UUID, update_data: RoleUpdateInDB) -> Role:
        """Update a role by its ID."""
        pass

    @abstractmethod
    async def add_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> Role:
        """Add a permission to a role."""
        pass

    @abstractmethod
    async def set_permissions(self, db: AsyncSession, role_id: UUID, permission_ids: List[UUID]) -> Role:
        """Replace all permissions of a role with the provided list."""
        pass

    @abstractmethod
    async def remove_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> Role:
        """Remove a permission from a role."""
        pass

    @abstractmethod
    async def has_permission(self, db: AsyncSession, role_id: UUID, permission_id: UUID) -> bool:
        """Return True if the role already has the given permission association."""
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, role_id: UUID) -> None:
        """Delete a role by its ID."""
        pass
