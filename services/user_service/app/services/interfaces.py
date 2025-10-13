from typing import Protocol
from app.schemas.user import UserCreate
from app.models.user import User

class IUserService(Protocol):
    def create(self, payload: UserCreate) -> User:
        ...
    def read(self, user_id: str) -> User:
        ...