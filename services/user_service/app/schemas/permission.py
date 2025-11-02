from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class PermissionBase(BaseModel):
    name: str = Field(..., example = "users:create", description = "The unique permission name")
    description: Optional[str] = Field(None, example = "Allows creating users", description = "Description of the permission")

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, example = "users:create", description = "The updated permission name")
    description: Optional[str] = Field(None, example = "Allows creating users", description = "Updated description")

class PermissionUpdateInDB(BaseModel):
    """Internal DTO for repository updates of Permission."""
    name: Optional[str] = Field(None, example = "users:create", description = "The updated permission name")
    description: Optional[str] = Field(None, example = "Allows creating users", description = "Updated description")

    model_config = {"from_attributes": True}

class PermissionRead(PermissionBase):
    id: UUID = Field(..., example = "a32a0d4b-0a4f-4d98-xxxx-8f7c2c3e9a0a", description = "Unique permission identifier")
    created_at: Optional[datetime] = Field(None, example = "2025-01-01T12:00:00Z", description = "Creation timestamp")
    updated_at: Optional[datetime] = Field(None, example = "2025-01-02T12:00:00Z", description = "Last update timestamp")

    model_config = {"from_attributes": True}
