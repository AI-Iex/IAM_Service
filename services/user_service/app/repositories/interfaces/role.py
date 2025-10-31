from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
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
                                name: Optional[str] = None, 
                                description: Optional[str] = None,
                                skip: int = 0, 
                                limit: int = 100
                            ) -> List[Role]:
        """Get roles with filters."""
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, role_id: UUID, role: RoleUpdate) -> Role:
        """Update a role by its ID."""
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, role_id: UUID) -> None:
        """Delete a role by its ID."""
        pass
