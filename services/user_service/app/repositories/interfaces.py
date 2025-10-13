from typing import Protocol, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreateInDB

class IUserRepository(Protocol):
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        ...

    def create(self, db: Session, dto: UserCreateInDB) -> User:
        ...
