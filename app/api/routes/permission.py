from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from typing import List, Optional
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate
from app.services.permission import PermissionService
from app.dependencies.services import get_permission_service
from app.schemas.auth import Principal
from app.core.permissions import requires_permission
from app.core.permissions_loader import Permissions

router = APIRouter(prefix="/permissions", tags=["Permissions"])


# Create a new permission
@router.post(
    "",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new permission",
    description="**Create a new permission with the necessary fields:**\n"
    "- `Name`: The name of the permission.\n"
    "- `Description`: A brief description of the permission.\n",
    response_description="The created permission",
)
async def create_permission(
    payload: PermissionCreate,
    permission_service: PermissionService = Depends(get_permission_service),
    principal: Principal = requires_permission(Permissions.PERMISSIONS_CREATE),
) -> PermissionRead:
    return await permission_service.create(payload)


# Read permissions with filters
@router.get(
    "",
    response_model=List[PermissionRead],
    status_code=status.HTTP_200_OK,
    summary="Get permissions with filtering and pagination",
    description="**Retrieve permissions with optional filtering, don't fill anything to get all the permissions.**\n"
    "- `Name`: Partial name search.\n"
    "- `Description`: Partial description search.\n"
    "- `Pagination`: Use `skip` (offset) and `limit` (max records) for pagination.",
    response_description="List of permissions matching criteria",
)
async def read_permissions(
    name: Optional[str] = Query(None, description="Partial name search"),
    description: Optional[str] = Query(None, description="Partial description search"),
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(100, ge=1, le=100, description="Limit"),
    permission_service: PermissionService = Depends(get_permission_service),
    principal: Principal = requires_permission(Permissions.PERMISSIONS_READ),
) -> List[PermissionRead]:
    return await permission_service.read_with_filters(name=name, description=description, skip=skip, limit=limit)


# Read permission by ID
@router.get(
    "/{permission_id}",
    response_model=PermissionRead,
    status_code=status.HTTP_200_OK,
    summary="Get permission by ID",
    description="**Retrieve a permission by its unique identifier.**\n"
    "- `permission_id`: The unique identifier of the permission.",
    response_description="The permission with the specified ID",
)
async def read_permission(
    permission_id: UUID,
    permission_service: PermissionService = Depends(get_permission_service),
    principal: Principal = requires_permission(Permissions.PERMISSIONS_READ),
) -> PermissionRead:
    return await permission_service.read_by_id(permission_id)


# Update permission by ID
@router.patch(
    "/{permission_id}",
    response_model=PermissionRead,
    status_code=status.HTTP_200_OK,
    summary="Update permission by ID",
    description="**Update a permission by its unique identifier.**\n"
    "- `name`: The updated permission name.\n"
    "- `description`: The updated permission description.",
    response_description="The updated permission",
)
async def update_permission(
    permission_id: UUID,
    payload: PermissionUpdate,
    permission_service: PermissionService = Depends(get_permission_service),
    principal: Principal = requires_permission(Permissions.PERMISSIONS_UPDATE),
) -> PermissionRead:
    return await permission_service.update(permission_id, payload)


# Delete permission by ID
@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete permission by ID",
    description="**Delete a permission by its unique identifier.**\n"
    "- `permission_id`: The unique identifier of the permission.",
)
async def delete_permission(
    permission_id: UUID,
    permission_service: PermissionService = Depends(get_permission_service),
    principal: Principal = requires_permission(Permissions.PERMISSIONS_DELETE),
) -> None:
    await permission_service.delete(permission_id)
