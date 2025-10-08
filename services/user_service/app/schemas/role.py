from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# Base schema with common fields
class RoleBase(BaseModel):
    name: str = Field(..., example = "admin", description = "The name of the role")

# Schema for role creation (inherits from RoleBase)
class RoleCreate(RoleBase):
    pass

# Schema for reading role data (includes id)
class RoleRead(RoleBase):
    id: int = Field(..., example = 1, description = "The unique identifier of the role")

    model_config = {"from_attributes": True}

# Schema for know if the role is in the database
class RoleInDB(RoleBase):
    id: int = Field(..., example = 1, description = "The unique identifier of the role")

    model_config = {"from_attributes": True}
    pass