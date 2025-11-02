from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from app.schemas.permission import PermissionRead

class RoleBase(BaseModel):
    name: str = Field(..., example = "admin", description = "The name of the role")
    description: Optional[str] = Field(None, example = "Administrator with full access", description = "Description of the role")

class RoleCreate(RoleBase):
    permissions: Optional[List[str]] = Field(default = [], example = ["view_users", "edit_users"], description = "List of permission names assigned to this role")

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, example = "manager", description = "Updated role name")
    description: Optional[str] = Field(None, example = "Manager role", description = "Updated role description")
    permissions: Optional[List[str]] = Field(default = None, example = ["users_create, users_delete"], description = "Updated list of permissions")


class RoleUpdateInDB(BaseModel):
    """Internal DTO for repository updates of Role."""
    name: Optional[str] = Field(None, example = "manager", description = "Updated role name")
    description: Optional[str] = Field(None, example = "Manager role", description = "Updated role description")

    model_config = {"from_attributes": True}

class RoleRead(RoleBase):
    id: UUID = Field(..., example = "d44b9c8f-4b36-4ffb-xxxx-1f0b70cced7d", description = "Unique role identifier")
    created_at: Optional[datetime] = Field(None, example = "2025-01-01T12:00:00Z", description = "Creation timestamp")
    updated_at: Optional[datetime] = Field(None, example = "2025-01-02T12:00:00Z", description = "Last update timestamp")
    permissions: List[PermissionRead] = Field(default = [], example = ["""view_users","edit_roles"""], description = "List of permissions names assigned to this role")

    model_config = {"from_attributes": True}

class RoleReadWithoutPermissions(RoleBase):
    id: UUID = Field(..., example = "d44b9c8f-4b36-4ffb-xxxx-1f0b70cced7d", description = "Unique role identifier")
    created_at: Optional[datetime] = Field(None, example = "2025-01-01T12:00:00Z", description = "Creation timestamp")
    updated_at: Optional[datetime] = Field(None, example = "2025-01-02T12:00:00Z", description = "Last update timestamp")
    
    model_config = {"from_attributes": True}
