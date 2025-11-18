from fastapi import APIRouter, Depends, Path, Query, status, HTTPException, Response, Request, Header
from uuid import UUID
from typing import List, Optional
from app.schemas.user import UserRead
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.role import RoleService
from app.dependencies.services import get_role_service
from app.schemas.auth import Principal
from app.core.permissions import requires_permission
from app.core.permissions_loader import Permissions

router = APIRouter(prefix="/roles", tags=["Roles"])


# Create a new role
@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    description="**Create a new role with the necessary fields:**\n"
    "- `Name`: The name of the role.\n"
    "- `Description`: A brief description of the role.\n"
    "- `Permissions`: List of permissions (permission name + service_name) assigned to this role.\n",
    response_description="The created role",
)
async def create_role(
    payload: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
    principal: Principal = requires_permission(Permissions.ROLES_CREATE),
) -> RoleRead:
    return await role_service.create(payload)


# Read roles with filters
@router.get(
    "",
    response_model=List[RoleRead],
    status_code=status.HTTP_200_OK,
    summary="Get roles with filtering and pagination",
    description="**Retrieve roles with optional filtering, don't fill anything to get all the roles.**\n"
    "- `Name`: Partial name search.\n"
    "- `Description`: Partial description search.\n"
    "- `Pagination`: Use `skip` (offset) and `limit` (max records) for pagination.",
    response_description="List of roles matching criteria",
)
async def read_roles(
    name: Optional[str] = Query(None, description="Partial name search"),
    description: Optional[str] = Query(None, description="Partial description search"),
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)"),
    limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
    role_service: RoleService = Depends(get_role_service),
    principal: Principal = requires_permission(Permissions.ROLES_READ),
) -> List[RoleRead]:
    return await role_service.read_with_filters(name=name, description=description, skip=skip, limit=limit)


# Read role by ID
@router.get(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Get role by ID",
    description="**Retrieve a role by its unique identifier.**\n" "- `role_id`: The unique identifier of the role.",
    response_description="The role with the specified ID",
)
async def read_role(
    role_id: UUID = Path(..., description="Unique role identifier"),
    role_service: RoleService = Depends(get_role_service),
    principal: Principal = requires_permission(Permissions.ROLES_READ),
) -> RoleRead:
    return await role_service.read_by_id(role_id)


# Update role by ID
@router.patch(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Update role by ID",
    description="**Update a role by its unique identifier.**\n"
    "- `name`: The updated role name.\n"
    "- `description`: The updated role description.\n"
    "- `permissions`: List of permissions assigned to this role. Setting this field will replace all existing permissions of the role with the provided list,"
    " and setting an empty list will remove all permissions from the role.\n",
    response_description="The updated role",
)
async def update_role(
    role_id: UUID = Path(..., description="Unique role identifier"),
    payload: RoleUpdate = ...,
    role_service: RoleService = Depends(get_role_service),
    principal: Principal = requires_permission(Permissions.ROLES_UPDATE),
) -> RoleRead:
    return await role_service.update(role_id, payload)


# Add a permission to a role
@router.post(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Add permission to role",
    description="**Assign a permission to a role.**\n"
    "- `role_id`: Unique identifier of the role.\n"
    "- `permission_id`: Unique identifier of the permission to add.",
    response_description="Role with the added permission",
)
async def add_permission_to_role(
    role_id: UUID = Path(..., description="Unique role identifier"),
    permission_id: UUID = Path(..., description="Unique permission identifier"),
    role_service: RoleService = Depends(get_role_service),
    principal: Principal = requires_permission(Permissions.ROLES_UPDATE),
) -> RoleRead:
    return await role_service.assign_permission(role_id, permission_id)


# Remove a permission from a role
@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Remove permission from role",
    description="**Remove the specified permission from a role.**\n"
    "- `role_id`: Unique identifier of the role.\n"
    "- `permission_id`: Unique identifier of the permission to remove.",
    response_description="Role with the permission removed",
)
async def remove_permission_from_role(
    role_id: UUID = Path(..., description="Unique role identifier"),
    permission_id: UUID = Path(..., description="Unique permission identifier"),
    role_service: RoleService = Depends(get_role_service),
    principal: Principal = requires_permission(Permissions.ROLES_UPDATE),
) -> RoleRead:
    return await role_service.remove_permission(role_id, permission_id)


# Delete role by ID
@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete role by ID",
    description="**Delete a role by its unique identifier.**\n" "- `role_id`: The unique identifier of the role.",
)
async def delete_role(
    role_id: UUID = Path(..., description="Unique role identifier"),
    role_service: RoleService = Depends(get_role_service),
    principal: Principal = requires_permission(Permissions.ROLES_DELETE),
) -> None:
    await role_service.delete(role_id)
