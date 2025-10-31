from fastapi import (
    APIRouter, Depends, Query, status, HTTPException, Response, Request, Header
)
from uuid import UUID
from typing import List, Optional
from app.schemas.user import UserRead
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.role import RoleService
from app.dependencies.services import get_role_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/roles", tags=["Roles"])

# Create a new role
@router.post(
    "",
    response_model = RoleRead,
    status_code = status.HTTP_201_CREATED,
    summary = "Create a new role",
    description = "Create a new role with the necessary fields:\n"
                "- `Name`: The name of the role.\n"
                "- `Description`: A brief description of the role.\n",
    response_description = "The created role"
)
async def create_role(
    payload: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = Depends(get_current_user)
) -> RoleRead:
    return await role_service.create(payload)

# Read roles with filters
@router.get(
    "",
    response_model = List[RoleRead],
    status_code = status.HTTP_200_OK,
    summary = "Get roles with filtering and pagination",
    description = "Retrieve a list of all roles with optional filters.",
    response_description = "List of roles matching criteria"
)
async def read_roles(
    name: Optional[str] = Query(None, description = "Partial name search"),
    description: Optional[str] = Query(None, description = "Partial description search"),
    skip: int = Query(0, ge = 0, description = "Number of records to skip (offset)"),
    limit: int = Query(100, ge = 1, le = 100, description = "Maximum records to return"),
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = Depends(get_current_user)
) -> List[RoleRead]:
    return await role_service.read_with_filters(
        name = name, description = description,
        skip = skip, limit = limit
    )

# Read role by ID
@router.get(
    "/{role_id}",
    response_model = RoleRead,
    status_code = status.HTTP_200_OK,
    summary = "Get role by ID",
    description = "Retrieve a role by its unique identifier.",
    response_description = "The role with the specified ID"
)
async def read_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = Depends(get_current_user)
) -> RoleRead:
    return await role_service.read_by_id(role_id)

# Update role by ID
@router.put(
    "/{role_id}",
    response_model = RoleRead,
    status_code = status.HTTP_200_OK,
    summary = "Update role by ID",
    description = "Update a role by its unique identifier.",
    response_description = "The updated role"
)
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = Depends(get_current_user)
) -> RoleRead:
    return await role_service.update(role_id, payload)

# Delete role by ID
@router.delete(
    "/{role_id}",
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Delete role by ID",
    description = "Delete a role by its unique identifier."
)
async def delete_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = Depends(get_current_user)
) -> None:
    await role_service.delete(role_id)