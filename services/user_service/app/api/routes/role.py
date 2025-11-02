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
from uuid import UUID
from app.core.permissions import requires_permission

router = APIRouter(prefix="/roles", tags=["Roles"])

# Create a new role
@router.post(
    "",
    response_model = RoleRead,
    status_code = status.HTTP_201_CREATED,
    summary = "Create a new role",
    description = "**Create a new role with the necessary fields:**\n"
                "- `Name`: The name of the role.\n"
                "- `Description`: A brief description of the role.\n",
    response_description = "The created role"
)
async def create_role(
    payload: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = requires_permission("roles:create")
) -> RoleRead:
    return await role_service.create(payload)


# Read roles with filters
@router.get(
    "",
    response_model = List[RoleRead],
    status_code = status.HTTP_200_OK,
    summary = "Get roles with filtering and pagination",
    description = "**Retrieve roles with optional filtering, don't fill anything to get all the roles.**\n" 
    "- `Name`: Exact name match (can provide multiple names).\n"
    "- `Description`: Partial description search.\n"
    "- `Pagination`: Use `skip` (offset) and `limit` (max records) for pagination.",
    response_description = "List of roles matching criteria"
)
async def read_roles(
    name: Optional[List[str]] = Query(None, description = "Exact name match (can provide multiple names)"),
    description: Optional[str] = Query(None, description = "Partial description search"),
    skip: int = Query(0, ge = 0, description = "Number of records to skip (offset)"),
    limit: int = Query(100, ge = 1, le = 100, description = "Maximum records to return"),
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = requires_permission("roles:read")
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
    description = "**Retrieve a role by its unique identifier.**\n"
    "- `role_id`: The unique identifier of the role.",
    response_description = "The role with the specified ID"
)
async def read_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = requires_permission("roles:read")
) -> RoleRead:
    return await role_service.read_by_id(role_id)


# Update role by ID
@router.patch(
    "/{role_id}",
    response_model = RoleRead,
    status_code = status.HTTP_200_OK,
    summary = "Update role by ID",
    description = "**Update a role by its unique identifier.**\n"
    "- `name`: The updated role name.\n"
    "- `description`: The updated role description.",
    response_description = "The updated role"
)
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = requires_permission("roles:update")
) -> RoleRead:
    return await role_service.update(role_id, payload)


# Delete role by ID
@router.delete(
    "/{role_id}",
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Delete role by ID",
    description = "**Delete a role by its unique identifier.**\n" \
    "- `role_id`: The unique identifier of the role."
)
async def delete_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = requires_permission("roles:delete")
) -> None:
    await role_service.delete(role_id)


# Add a permission to a role
@router.post(
    "/{role_id}/permissions/{permission_id}",
    response_model = RoleRead,
    status_code = status.HTTP_200_OK,
    summary = "Add permission to role",
    description = "**Assign a permission to a role.**\n"
    "- `role_id`: Unique identifier of the role.\n"
    "- `permission_id`: Unique identifier of the permission to add.",
    response_description = "Role with the added permission"
)
async def add_permission_to_role(
    role_id: UUID,
    permission_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = requires_permission("roles:update")
) -> RoleRead:
    return await role_service.add_permission(role_id, permission_id)


# Remove a permission from a role
@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model = RoleRead,
    status_code = status.HTTP_200_OK,
    summary = "Remove permission from role",
    description = "**Remove the specified permission from a role.**\n" \
    "- `role_id`: Unique identifier of the role.\n"
    "- `permission_id`: Unique identifier of the permission to remove.",
    response_description = "Role with the permission removed"
)
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: UserRead = requires_permission("roles:update")
) -> RoleRead:
    return await role_service.remove_permission(role_id, permission_id)