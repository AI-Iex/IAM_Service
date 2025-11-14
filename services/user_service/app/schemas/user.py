from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from app.schemas.role import RoleReadWithoutPermissions, RoleRead

# Base schema with common fields
class UserBase(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "user@gmail.com"}, description = "The user's email address")
    full_name: str = Field(..., json_schema_extra={"example": "Name Surname"}, description = "The user's name and surname")
    is_active: bool = Field(default = True, json_schema_extra={"example": True}, description = "Is the user active?")
    is_superuser: bool = Field(default = False, json_schema_extra={"example": False}, description = "Is the user a superuser for get all permissions?")


# Schema for self-service user registration
class UserRegister(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "user@gmail.com"}, description = "The user's email address")
    full_name: str = Field(..., json_schema_extra={"example": "Name Surname"}, description = "The user's name and surname")
    password: str = Field(..., json_schema_extra={"example": "strongpassword123"}, repr = False, description = "The user's password")


# Schema for user creation by admin (includes temporary password)
class UserCreateByAdmin(UserBase):
    password: str = Field(..., json_schema_extra={"example": "strongpassword123"}, repr = False, description = "The user's password")


# Internal schema for user creation in DB (includes hashed_password, used by repository)
class UserCreateInDB(UserBase):
    hashed_password: str = Field(..., description = "The hashed password of the user", repr = False)
    require_password_change: bool = Field(default = False, json_schema_extra={"example": False}, description = "Flag to force the user change the password")

    model_config = {"from_attributes": True}


# Schema for user update (all fields optional)
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, json_schema_extra={"example": "Name Surname"}, description = "The user's name and surname")
    is_active: Optional[bool] = Field(None, json_schema_extra={"example": True}, description = "Is the user active?")
    is_superuser: Optional[bool] = Field(None, json_schema_extra={"example": False}, description = "Is the user a superuser for get all permissions?")
    roles: Optional[List[str]] = Field(None, json_schema_extra={"example": ["admin", "developer"]}, description = "List of roles assigned to the user")


class UserUpdateInDB(BaseModel):
    """Internal schema used by services when passing update payloads to repositories."""
    email: Optional[str] = Field(None, json_schema_extra={"example": "user@gmail.com"}, description = "The user's email address")
    full_name: Optional[str] = Field(None, json_schema_extra={"example": "Name Surname"}, description = "The user's name and surname")
    hashed_password: Optional[str] = Field(None, description = "The hashed password of the user", repr = False)
    is_active: Optional[bool] = Field(None, json_schema_extra={"example": True}, description = "Is the user active?")
    is_superuser: Optional[bool] = Field(None, json_schema_extra={"example": False}, description = "Is the user a superuser for get all permissions?")
    require_password_change: Optional[bool] = Field(None, description = "Flag to force the user change the password")
    roles: Optional[List] = Field(None, description = "Roles to assign (can be ORM role entities when passed from service)")

    model_config = {"from_attributes": True}


# Schema for change the user email
class UserChangeEmail(BaseModel):
    current_email: str = Field(..., json_schema_extra={"example": "currentemail@email.com"}, description = "Current email address for verification")
    new_email: str = Field(..., json_schema_extra={"example": "newemail@email.com"}, description = "The new email address")
    current_password: str = Field(..., json_schema_extra={"example": "CurrentPassword123!"}, description = "Current password for verification")


# Schema for reading user data (includes id, timestamps, and roles)
class UserRead(UserBase):
    id: UUID = Field(..., json_schema_extra={"example": "c55df1d2-216a-4359-81xx-1d805801vg0g"}, description = "Unique user identifier")
    created_at: Optional[datetime] = Field(None, json_schema_extra={"example": "2023-01-01T00:00:00Z"}, description = "The date and time when the user was created")
    updated_at: Optional[datetime] = Field(None, json_schema_extra={"example": "2023-01-05T15:30:00Z"}, description = "The date and time when the user was last updated")
    last_login: Optional[datetime] = Field(None, json_schema_extra={"example": "2023-01-10T12:34:56Z"}, description = "The date and time of the user's last login")
    roles: List[RoleReadWithoutPermissions] = Field(default = [], json_schema_extra={"example": ["admin", "user"]}, description = "List of roles assigned to the user")
    require_password_change: bool = Field(default = False, json_schema_extra={"example": False}, description = "Flag to force the user change the password")

    model_config = {"from_attributes": True}

# Schema for reading user data with detailed roles and permissions
class UserReadDetailed(UserRead):
    roles: List[RoleRead] = Field(default = [], json_schema_extra={"example": ["admin", "user"]}, description = "List of roles assigned to the user")


# Schema for user login (used for authentication)
class UserLogin(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "user@email.com"}, description = "The user's email")
    password: str = Field(..., json_schema_extra={"example": "strongpassword123"}, description = "The user's password",  repr = False) 


# Internal schema for know if the user is in the database
class UserInDB(UserBase):
    id: UUID = Field(..., json_schema_extra={"example": "c55df1d2-216a-4359-81xx-1d805801vg0g"}, description = "Unique user identifier")
    hashed_password: str = Field(..., description = "The hashed password of the user", repr = False)
    roles: List[RoleReadWithoutPermissions] = Field(default = [], json_schema_extra={"example": ["admin", "user"]}, description = "List of roles assigned to the user")

    model_config = {"from_attributes": True}


# Schema for password change
class PasswordChange(BaseModel):
    old_password: str = Field(..., json_schema_extra={"example": "oldpassword123"}, description = "The user's current password", repr = False)
    new_password: str = Field(..., json_schema_extra={"example": "newstrongpassword123"}, description = "The new password for the user", repr = False)