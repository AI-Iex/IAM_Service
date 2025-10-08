from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import EmailStr
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserRead, UserLogin, UserInDB, PasswordChange
from app.models.user import User
from app.models.role import Role

class UserRepository:

# region CREATE

    # Function to create a new user
    def create(self, db: Session, user_data: UserBase, hashed_password: str) -> User:
        pass

# endregion CREATE

# region READ

    # Function to get a user by ID
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        pass

    # Function to get a user by email
    def get_by_email(self, db: Session, email: EmailStr) -> Optional[User]:
        pass

    # Function to get all users with pagination
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        pass

    # Function to get all the active users with pagination
    def get_all_active(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        pass

    # Function to get all the superusers with pagination
    def get_all_superusers(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        pass

# endregion READ

# region UPDATE

    # Function to update a user
    def update(db: Session, user_id: int, user: UserUpdate) -> Optional[UserRead]:
        pass

    # Function to update the last login timestamp
    def update_last_login(db: Session, user_id: int, last_login) -> Optional[UserRead]:
        pass

# endregion UPDATE

# region DELETE

    # Function to delete a user
    def delete(db: Session, user_id: int) -> bool:
       pass

# endregion DELETE