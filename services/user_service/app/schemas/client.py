from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from app.schemas.permission import PermissionRead, PermissionRef


class ClientBase(BaseModel):
    name: str = Field(..., example = "My Client App", description = "The name of the client application")


class ClientCreate(ClientBase):
    is_active: bool = Field(True, example = True, description = "Indicates if the client account is active")
    pass


class ClientCreateInDB(ClientCreate):
    secret_hashed: str = Field(..., description = "Generated client secret hashed")
    client_id: UUID = Field(..., example = "a32a0d4b-0a4f-4d98-xxxx-8f7c2c3e9a0a", description = "Public client identifier used for authentication")
    pass

class ClientRead(ClientBase):
    id: UUID = Field(..., example = "a32a0d4b-0a4f-4d98-xxxx-8f7c2c3e9a0a", description = "Unique client identifier")
    client_id: UUID = Field(..., example = "a32a0d4b-0a4f-4d98-xxxx-8f7c2c3e9a0a", description = "Public client identifier")
    is_active: bool = Field(True, example = True, description = "Indicates if the client account is active")
    created_at: Optional[datetime] = Field(None, example = "2025-01-01T12:00:00Z", description = "Creation timestamp")
    permissions: Optional[List[PermissionRead]] = Field(
        None,
        example = [{"name": "users:read"}, {"name": "roles:create"}],
        description = "List of permission reference objects assigned to this client"
    )

    model_config = {"from_attributes": True}


class ClientCreateResponse(ClientRead):
    secret: str = Field(..., example = "generated-secret", description = "Generated client secret (save it securely!)")


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, example = "Updated Client", description = "Updated client name")
    is_active: Optional[bool] = Field(None, example = True, description = "Updated active status")
    permissions: Optional[List[PermissionRef]] = Field(None, example = [{"name": "users:read"}, {"name": "roles:create"}], description = "List of permission reference objects assigned to this client")


class ClientUpdateInDB(BaseModel):
    """Internal DTO for repository updates of Client."""
    name: Optional[str] = Field(None, example = "Updated Client", description = "Updated client name")
    is_active: Optional[bool] = Field(None, example = True, description = "Updated active status")

    model_config = {"from_attributes": True}


class ClientPermissionAssign(BaseModel):
    permissions: List[str] = Field(..., example = ["users:read", "roles:create"], description = "List of permission names to assign to the client")


class ClientPermissionAssignById(BaseModel):
    permission_ids: List[UUID] = Field(..., example = ["a32a0d4b-0a4f-4d98-xxxx-8f7c2c3e9a0a", "b32a0d4b-0a4f-4d98-xxxx-8f7c2c3e9a0b"], description = "List of permission IDs to assign to the client")