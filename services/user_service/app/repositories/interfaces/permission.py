from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionUpdateInDB


class IPermissionRepository(ABC):

    @abstractmethod
    async def create(self, db: AsyncSession, payload: PermissionCreate) -> Permission:
        '''Create a Permission returning the created object.'''
        pass

    @abstractmethod
    async def read_by_id(self, db: AsyncSession, permission_id: UUID) -> Optional[Permission]:
        '''Retrieve a permission by id.'''
        pass

    @abstractmethod
    async def read_with_filters(
        self,
        db: AsyncSession, 
        name: Optional[str] = None,
        service_name: Optional[str] = None,
        description: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Permission]:
        '''Retrieve permissions matching filters.'''
        pass

    @abstractmethod
    async def read_by_names(self, db: AsyncSession, names: List[str], service_name: Optional[str] = None) -> List[Permission]:
        '''Retrieve permissions matching provided names list.'''
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, permission_id: UUID, payload: PermissionUpdateInDB) -> Permission:
        '''Update a permission by id using internal DTO.'''
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, permission_id: UUID) -> None:
        '''Delete a permission by id.'''
        pass
