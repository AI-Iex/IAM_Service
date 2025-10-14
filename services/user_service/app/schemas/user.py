from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# Base schema with common fields
class UserBase(BaseModel):
    email: EmailStr = Field(..., example = "user@email.com", description="The user's email address")
    full_name: str = Field(..., example = "Name Surname", description="The user's full name")
    is_active: bool = Field(default = True, example = True, description="Is the user active?")
    is_superuser: bool = Field(default = False, example = False, description="Is the user a superuser for get all permissions?")

# Schema for user creation (includes password, received in service only, never used by repository)
class UserCreate(UserBase):
    password: str = Field(..., example = "strongpassword123", repr=False)

# Internal schema for user creation in DB (includes hashed_password, used by repository)
class UserCreateInDB(UserBase):
    hashed_password: str = Field(..., description="The hashed password of the user", repr=False)

    model_config = {"from_attributes": True}

# Schema for user update (all fields optional)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example = "user@email.com", description="The user's email address")
    full_name: Optional[str] = Field(None, example = "Name Surname", description="The user's full name")
    is_active: Optional[bool] = Field(None, example = True, description="Is the user active?")
    is_superuser: Optional[bool] = Field(None, example = False, description="Is the user a superuser for get all permissions?")
    roles: Optional[List[str]] = Field(None, example = ["admin", "user"], description="List of roles assigned to the user")

# Schema for reading user data (includes id, timestamps, and roles)
class UserRead(UserBase):
    id: int = Field(..., example = 1, description="The unique identifier of the user")
    created_at: Optional[datetime] = Field(None, example = "2023-01-01T00:00:00Z", description="The date and time when the user was created")
    last_login: Optional[datetime] = Field(None, example = "2023-01-10T12:34:56Z", description="The date and time of the user's last login")
    roles: List[str] = Field(default = [], example = ["admin", "user"], description="List of roles assigned to the user")

    model_config = {"from_attributes": True}

# Schema for user login (used for authentication)
class UserLogin(BaseModel):
    email: EmailStr = Field(..., example = "user@email.com", description="The user's email")
    password: str = Field(..., example = "strongpassword123", description="The user's password",  repr=False) 

# Internal schema for know if the user is in the database
class UserInDB(UserBase):
    id: int = Field(..., example = 1, description="The unique identifier of the user")
    hashed_password: str = Field(..., description="The hashed password of the user", repr=False)
    roles: List[str] = Field(default = [], example = ["admin", "user"], description="List of roles assigned to the user")

    model_config = {"from_attributes": True}

# Schema for password change
class PasswordChange(BaseModel):
    old_password: str = Field(..., example = "oldpassword123", description="The user's current password", repr=False)
    new_password: str = Field(..., example = "newstrongpassword123", description="The new password for the user", repr=False)