from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class PermissionBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "users:create"}, description = "The permission name")
    description: Optional[str] = Field(None, json_schema_extra={"example": "Allows creating users"}, description = "Description of the permission")

# used for create and update a role, to reference permissions
class PermissionRef(BaseModel):
    '''Reference DTO for Permission by name.'''
    name: str = Field(..., json_schema_extra={"example": "users:read"}, description="Permission name")

    model_config = {"from_attributes": True}

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, json_schema_extra={"example": "users:create"}, description = "The updated permission name")
    description: Optional[str] = Field(None, json_schema_extra={"example": "Allows creating users"}, description = "Updated description")

class PermissionUpdateInDB(BaseModel):
    """Internal DTO for repository updates of Permission."""
    name: Optional[str] = Field(None, json_schema_extra={"example": "users:create"}, description = "The updated permission name")
    description: Optional[str] = Field(None, json_schema_extra={"example": "Allows creating users"}, description = "Updated description")

    model_config = {"from_attributes": True}

class PermissionRead(PermissionBase):
    id: UUID = Field(..., json_schema_extra={"example": "a32a0d4b-0a4f-4d98-xxxx-8f7c2c3e9a0a"}, description = "Unique permission identifier")
    created_at: Optional[datetime] = Field(None, json_schema_extra={"example": "2025-01-01T12:00:00Z"}, description = "Creation timestamp")
    updated_at: Optional[datetime] = Field(None, json_schema_extra={"example": "2025-01-02T12:00:00Z"}, description = "Last update timestamp")

    model_config = {"from_attributes": True}
