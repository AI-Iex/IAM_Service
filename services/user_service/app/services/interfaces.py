from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.user import UserCreate, UserRead
from uuid import UUID

class IUserService(ABC):

    @abstractmethod
    async def create(self, payload: UserCreate) -> UserRead:
        pass

    @abstractmethod
    async def read_by_id(self, user_id: UUID) -> Optional[UserRead]:
        pass

    @abstractmethod
    async def read_by_email(self, email: str) -> Optional[UserRead]:
        pass

    @abstractmethod
    async def read_by_name(self, name: str, skip: int, limit: int) -> List[UserRead]:
        pass

    @abstractmethod
    async def update(self, user_id: UUID, payload) -> Optional[UserRead]:
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        pass

    @abstractmethod
    async def read_all(self, skip: int, limit: int) -> List[UserRead]:
        pass

    @abstractmethod
    async def read_active(self, skip: int, limit: int) -> List[UserRead]:
        pass

    @abstractmethod
    async def read_superusers(self, skip: int, limit: int) -> List[UserRead]:
        pass