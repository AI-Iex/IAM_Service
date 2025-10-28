# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID
from app.schemas.user import UserRead

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    jti: UUID
    roles: Optional[List[str]] = []
    is_superuser: Optional[bool] = False

class TokenPair(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    jti: Optional[UUID] = None
    token_type: str = "bearer"
    expires_in: int  

class AuthResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    token: TokenPair

class UserAndToken(BaseModel):
    user: UserRead
    token: TokenPair

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None