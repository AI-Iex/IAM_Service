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
    async def get_with_filters(
        self,
        db: AsyncSession,
        name: Optional[str] = None,
        email: Optional[str] = None, 
        active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        pass

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, user_id: UUID, update_data: UserUpdate) -> User:
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, user_id: UUID) -> bool:
        pass