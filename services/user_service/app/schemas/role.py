from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

# Base schema with common fields
class RoleBase(BaseModel):
    name: str = Field(..., example = "admin", description = "The name of the role")

# Schema for role creation (inherits from RoleBase)
class RoleCreate(RoleBase):
    pass

# Schema for reading role data (includes id)
class RoleRead(RoleBase):
    id: UUID = Field(..., example = "c55df1d2-216a-4359-81xx-1d805801vg0g", description = "Unique role identifier")

    model_config = {"from_attributes": True}

# Schema for know if the role is in the database
class RoleInDB(RoleBase):
    id: UUID = Field(..., example = "c55df1d2-216a-4359-81xx-1d805801vg0g", description = "Unique role identifier")

    model_config = {"from_attributes": True}
    pass