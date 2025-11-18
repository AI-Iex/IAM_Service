# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID
from app.schemas.user import UserRead
from app.schemas.user import UserReadDetailed
from app.schemas.client import ClientRead


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
    type: str = Field(default="user", description="Token type: 'user' or 'client'")
    roles: Optional[List[str]] = []
    is_superuser: Optional[bool] = False
    client_id: Optional[str] = None


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


class Principal(BaseModel):
    """Represents an authenticated principal (user or client)."""

    kind: str
    token: TokenPayload
    user: Optional[UserReadDetailed] = None
    client: Optional[ClientRead] = None


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class ClientAuthRequest(BaseModel):
    client_id: str = Field(..., description="The client identifier")
    client_secret: str = Field(..., description="The client secret")
    grant_type: str = Field(default="client_credentials", description="OAuth2 grant type")


class ClientAuthResponse(BaseModel):
    client_id: str
    token: TokenPair
