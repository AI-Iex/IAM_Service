from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserRead, UserLogin, UserInDB, PasswordChange
from app.repositories.user import UserRepository

# region CREATE

# Function to create a new user
def create(db: Session, user_data: UserCreate) -> User:
    try:
        # 1. Validate email format
        if "@" not in user_data.email:
            raise ValueError("Invalid email format")
        
        # 2. Verify the email is not already in use
        if UserRepository.get_by_email(db, user_data.email) is not None:
            raise ValueError("Email is already in use")
        
        # 3. Hash the password
        hashed_password = hash_password(user_data.password)

        # 4. Create the user in the database
        user_create = UserBase(
            email = user_data.email,
            full_name = user_data.full_name,
            is_active = user_data.is_active,
            is_superuser = user_data.is_superuser
        )
        
        return UserRepository.create(db, user_create, hashed_password)

    except Exception as e:
        print(f"Error creating user: {e}")
        return None

# endregion CREATE