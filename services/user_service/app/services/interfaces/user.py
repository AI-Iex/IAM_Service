from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.user import UserCreateByAdmin, UserRead, UserUpdate, UserChangeEmail, UserRegister
from uuid import UUID

class IUserService(ABC):

    @abstractmethod
    async def register_user(self, payload: UserRegister) -> UserRead:
        pass

    @abstractmethod
    async def admin_register_user(self, payload: UserCreateByAdmin) -> UserRead:
        pass

    @abstractmethod
    async def read_with_filters(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None, 
        active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRead]:
        pass

    @abstractmethod
    async def read_by_id(self, user_id: UUID) -> UserRead:
        pass

    @abstractmethod
    async def update(self, user_id: UUID, payload: UserUpdate) -> UserRead:
        pass

    @abstractmethod
    async def change_email(self, user_id: UUID, payload: UserChangeEmail) -> UserRead:
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        pass