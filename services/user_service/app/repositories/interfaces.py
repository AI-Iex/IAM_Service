from abc import ABC, abstractmethod
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreateInDB, UserUpdate
from uuid import UUID

class IUserRepository(ABC):

    @abstractmethod
    async def create(self, db: AsyncSession, dto: UserCreateInDB) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_name(self, db: AsyncSession, name: str, skip: int, limit: int) -> List[User]:
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, user_id: UUID, update_data: UserUpdate) -> Optional[User]:
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, user_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_all(self, db: AsyncSession, skip: int, limit: int) -> List[User]:
        pass