from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate


class IPermissionService(ABC):

    @abstractmethod
    async def create(self, payload: PermissionCreate) -> PermissionRead:
        pass

    @abstractmethod
    async def read_with_filters(self, 
                                name: Optional[str] = None, 
                                description: Optional[str] = None, 
                                skip: int = 0, 
                                limit: int = 100
                                ) -> List[PermissionRead]:
        pass

    @abstractmethod
    async def read_by_id(self, permission_id: UUID) -> PermissionRead:
        pass

    @abstractmethod
    async def update(self, permission_id: UUID, payload: PermissionUpdate) -> PermissionRead:
        pass

    @abstractmethod
    async def delete(self, permission_id: UUID) -> None:
        pass
