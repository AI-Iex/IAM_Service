from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreateInDB
from app.core.exceptions import EntityAlreadyExists, RepositoryError
from app.repositories.interfaces import IUserRepository

class UserRepository(IUserRepository):

# region CREATE

    # Create a new user in the database
    def create(self, db: Session, dto: UserCreateInDB) -> User:
        try:
            user = User(
                email=dto.email,
                full_name=dto.full_name,
                hashed_password=dto.hashed_password,
                is_active=dto.is_active,
                is_superuser=dto.is_superuser
            )
            db.add(user)
            db.flush()
            db.refresh(user)
            return user
        except IntegrityError as e:
            db.rollback()
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise EntityAlreadyExists("User with that email already exists") from e
            raise RepositoryError("Database integrity error") from e
        except Exception as e:
            db.rollback()
            raise RepositoryError("Unexpected database error") from e

# endregion CREATE

# region READ

    # Get a user by email
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    # Get a user by ID
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    # Get users by name
    def get_by_name(self, db: Session, name: str, skip: int = 0, limit: int = 100) -> list[User]:
        return (
            db.query(User)
              .filter(User.full_name.ilike(f"%{name}%"))
              .offset(skip)
              .limit(limit)
              .all()
        )

    
# endregion READ