from typing import Protocol
from app.schemas.user import UserCreate, UserRead
from app.models.user import User

class IUserService(Protocol):

    def create(self, payload: UserCreate) -> UserRead:
        ...

    def read_by_id(self, user_id: int) -> UserRead:
        ...

    def read_by_email(self, email: str) -> UserRead:
        ...

    def read_by_name(self, name: str, skip: int, limit: int) -> list[UserRead]:
        ...