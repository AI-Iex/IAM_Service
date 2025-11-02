from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.user import UserCreateByAdmin, UserRead, UserUpdate, UserChangeEmail, UserRegister, UserReadDetailed, PasswordChange
from uuid import UUID

class IUserService(ABC):

    @abstractmethod
    async def register_user(self, payload: UserRegister) -> UserRead:
        ''' Register a new user and return the created user data '''
        pass

    @abstractmethod
    async def admin_register_user(self, payload: UserCreateByAdmin) -> UserRead:
        ''' Register a new user by admin and return the created user data '''
        pass

    @abstractmethod
    async def read_with_filters(
        self,
        name: Optional[str] = None,
        email: Optional[List[str]] = None, 
        active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRead]:
        ''' Retrieve users matching the provided filters with pagination '''
        pass

    @abstractmethod
    async def read_by_id(self, user_id: UUID) -> UserRead:
        ''' Retrieve a user by its ID '''
        pass

    @abstractmethod
    async def read_by_id_detailed(self, user_id: UUID) -> UserReadDetailed:
        ''' Retrieve a user by its ID including detailed info like the permissions in their roles '''
        pass

    @abstractmethod
    async def update(self, user_id: UUID, payload: UserUpdate) -> UserRead:
        ''' Update a user by its ID '''
        pass

    @abstractmethod
    async def change_email(self, user_id: UUID, payload: UserChangeEmail) -> UserRead:
        ''' Change a user's email '''
        pass

    @abstractmethod
    async def change_password(self, user_id: UUID, payload: PasswordChange) -> UserRead:
        ''' Change a user's password '''
        pass

    @abstractmethod
    async def add_role_to_user(self, user_id: UUID, role_id: UUID) -> UserRead:
        ''' Add a role to a user '''
        pass

    @abstractmethod
    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> UserRead:
        ''' Remove a role from a user '''
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        ''' Delete a user by its ID '''
        pass