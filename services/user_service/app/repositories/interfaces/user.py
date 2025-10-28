from abc import ABC, abstractmethod
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreateInDB, UserUpdate
from uuid import UUID

class IUserRepository(ABC):

    @abstractmethod
    async def create(self, db: AsyncSession, dto: UserCreateInDB) -> User:
        ''' Create and persist a User row returning the created object '''
        pass

    @abstractmethod
    async def get_with_filters(
        self,
        db: AsyncSession,
        name: Optional[str] = None,
        email: Optional[str] = None, 
        active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        require_password_change: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        ''' Retrieve users matching the provided filters with pagination '''
        pass

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        ''' Retrieve a user by its ID '''
        pass

    @abstractmethod
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        ''' Retrieve a user by its email '''
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, user_id: UUID, update_data: UserUpdate) -> User:
        ''' Update a user by its ID '''
        pass

    @abstractmethod
    async def update_last_login(self, db: AsyncSession, user_id: UUID) -> User:
        ''' Update the last login timestamp for a user '''
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, user_id: UUID) -> None:
        ''' Delete a user by its ID '''
        pass