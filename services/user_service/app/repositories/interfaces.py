from typing import Protocol, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreateInDB

class IUserRepository(Protocol):

    def create(self, db: Session, dto: UserCreateInDB) -> User:
        ...
    
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        ...

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        ...

    def get_by_name(self, db: Session, name: str, skip: int, limit: int) -> list[User]:
        ...

    