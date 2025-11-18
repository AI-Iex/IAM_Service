from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from uuid import UUID
from typing import List, Optional
from app.schemas.client import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
    ClientPermissionAssign,
    ClientCreateResponse,
    ClientPermissionAssignById,
)
from app.schemas.user import UserRead
from app.services.client import ClientService
from app.dependencies.services import get_client_service
from app.schemas.auth import Principal
from app.core.security import AccessTokenType
from app.core.permissions import requires_permission
from app.core.permissions_loader import Permissions

router = APIRouter(prefix="/clients", tags=["Clients"])


# Create a new client
@router.post(
    "",
    response_model=ClientCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
    description="**Create a new client application account.**\n"
    "\n**The system will generate a unique `client_id` and a secure `secret` for authentication purposes. Saved securely! Will only be shown once at creation time.**\n"
    "- `name`: Name of the client application.\n"
    "- `is_active`: Indicates if the client account is active.",
    response_description="The created client with generated credentials",
)
async def create_client(
    payload: ClientCreate,
    client_service: ClientService = Depends(get_client_service),
    principal: Principal = requires_permission(Permissions.CLIENTS_CREATE),
) -> ClientCreateResponse:
    return await client_service.create(payload)


# Read clients with filters
@router.get(
    "",
    response_model=List[ClientRead],
    status_code=status.HTTP_200_OK,
    summary="Get clients with filtering and pagination",
    description="**Retrieve clients with optional filtering, don't fill anything to get all the clients.**\n"
    "- `name`: Partial name search.\n"
    "- `is_active`: Filter by active status.\n"
    "- `Pagination`: Use `skip` (offset) and `limit` (max records) for pagination.",
    response_description="List of clients matching criteria",
)
async def read_clients(
    name: Optional[str] = Query(None, description="Partial name search"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(100, ge=1, le=100, description="Limit"),
    client_service: ClientService = Depends(get_client_service),
    principal: Principal = requires_permission(Permissions.CLIENTS_READ),
) -> List[ClientRead]:
    return await client_service.read_with_filters(name=name, is_active=is_active, skip=skip, limit=limit)


# Read current client profile
@router.get(
    "/me",
    response_model=ClientRead,
    status_code=status.HTTP_200_OK,
    summary="Get current client profile",
    description="**Get the profile of the currently authenticated client**",
    response_description="The current client",
)
async def get_current_client_profile(
    principal: Principal = requires_permission(Permissions.CLIENTS_READ),
) -> ClientRead:

    # Ensure the principal is a client
    if principal.kind != AccessTokenType.CLIENT.value or not principal.client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a client token")

    return principal.client


# Read client by ID
@router.get(
    "/{client_id}",
    response_model=ClientRead,
    status_code=status.HTTP_200_OK,
    summary="Get client by ID",
    description="**Retrieve a client by its unique identifier.**\n"
    "- `client_id`: The unique identifier of the client.",
    response_description="The client with the specified ID",
)
async def read_client(
    client_id: UUID = Path(..., description="Unique client identifier"),
    client_service: ClientService = Depends(get_client_service),
    principal: Principal = requires_permission(Permissions.CLIENTS_READ),
) -> ClientRead:
    return await client_service.read_by_id(client_id)


# Update client by ID
@router.patch(
    "/{client_id}",
    response_model=ClientRead,
    status_code=status.HTTP_200_OK,
    summary="Update client by ID",
    description="**Update a client by its unique identifier.**\n"
    "- `name`: Updated client name.\n"
    "- `is_active`: Updated active status.\n"
    "- `permissions`: List of permissions assigned to this client. Setting this field will replace all existing permissions of the client with the provided list,"
    " and setting an empty list will remove all permissions from the client.",
    response_description="The updated client",
)
async def update_client(
    client_id: UUID = Path(..., description="Unique client identifier"),
    payload: ClientUpdate = None,
    client_service: ClientService = Depends(get_client_service),
    principal: Principal = requires_permission(Permissions.CLIENTS_UPDATE),
) -> ClientRead:
    return await client_service.update(client_id, payload)


# Assign permissions to client by IDs
@router.post(
    "/{client_id}/permissions/{permission_id}",
    response_model=ClientRead,
    status_code=status.HTTP_200_OK,
    summary="Assign permissions to client by IDs",
    description="**Assign a list of permissions to a client by their IDs.**\n"
    "- `permission_ids`: List of permission IDs to assign.",
    response_description="The updated client with assigned permissions",
)
async def assign_client_permissions_by_ids(
    client_id: UUID = Path(..., description="Unique client identifier"),
    permission_id: UUID = Path(..., description="Unique permission identifier"),
    client_service: ClientService = Depends(get_client_service),
    principal: Principal = requires_permission(Permissions.CLIENTS_UPDATE),
) -> ClientRead:
    return await client_service.assign_permission(client_id, permission_id)


# Remove permission from client by ID
@router.delete(
    "/{client_id}/permissions/{permission_id}",
    response_model=ClientRead,
    status_code=status.HTTP_200_OK,
    summary="Remove permission from client by ID",
    description="**Remove a specific permission from a client by permission ID.**\n"
    "- `client_id`: The unique identifier of the client.\n"
    "- `permission_id`: The unique identifier of the permission to remove.",
    response_description="The updated client with the permission removed",
)
async def remove_client_permission(
    client_id: UUID = Path(..., description="Unique client identifier"),
    permission_id: UUID = Path(..., description="Unique permission identifier"),
    client_service: ClientService = Depends(get_client_service),
    principal: Principal = requires_permission(Permissions.CLIENTS_UPDATE),
) -> ClientRead:
    return await client_service.remove_permission(client_id, permission_id)


# Delete client by ID
@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete client by ID",
    description="**Delete a client by its unique identifier.**\n" "- `client_id`: The unique identifier of the client.",
)
async def delete_client(
    client_id: UUID = Path(..., description="Unique client identifier"),
    client_service: ClientService = Depends(get_client_service),
    principal: Principal = requires_permission(Permissions.CLIENTS_DELETE),
) -> None:
    await client_service.delete(client_id)
