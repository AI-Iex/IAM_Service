from fastapi import APIRouter, Depends, status, Query, Path, HTTPException
from typing import List, Optional
from uuid import UUID
from app.schemas.user import UserCreateByAdmin, UserRead, UserUpdate, UserChangeEmail, PasswordChange
from app.services.user import UserService
from app.dependencies.services import get_user_service
from app.dependencies.auth import get_current_principal
from app.schemas.auth import Principal
from app.core.permissions import requires_permission
from app.core.permissions_loader import Permissions

router = APIRouter(prefix="/users", tags=["Users"])


# Create a new user
@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="**Create a new user, the user created will have need to change the password after the first log in.**\n"
    "- `Full Name`: Name and surname of the user.\n"
    "- `Email`: Valid email address of the user.\n"
    "- `Password`: Temporary password for the user account.\n"
    "- `Is Active`: Boolean indicating if the user account is active.\n"
    "- `Is Superuser`: Boolean indicating if the user has superuser privileges.",
    response_description="The created user",
)
async def create_user(
    payload: UserCreateByAdmin,
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = requires_permission(Permissions.USERS_CREATE),
) -> UserRead:
    return await user_service.create(payload)


# Read users with filters
@router.get(
    "",
    response_model=List[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Get users with filtering and pagination",
    description="**Retrieve users with optional filtering, don't fill anything to get all the users.**\n"
    "- `Name`: Partial name search.\n"
    "- `Email`: Exact email match (can provide multiple emails).\n"
    "- `Active`: Filter by active status.\n"
    "- `Is Superuser`: Filter by superuser status.\n"
    "- `Pagination`: Use `skip` (offset) and `limit` (max records) for pagination.",
    response_description="List of users matching criteria",
)
async def read_with_filters(
    name: Optional[str] = Query(None, min_length=2, description="Partial name search"),
    email: Optional[List[str]] = Query(None, description="Exact email match"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    is_superuser: Optional[bool] = Query(None, description="Filter by superuser status"),
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)"),
    limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = requires_permission(Permissions.USERS_READ),
) -> List[UserRead]:
    return await user_service.read_with_filters(
        name=name, email=email, active=active, is_superuser=is_superuser, skip=skip, limit=limit
    )


# Read current user profile
@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="**Get the profile of the currently authenticated user**",
    response_description="The current user",
)
async def get_current_user_profile(principal: Principal = Depends(get_current_principal)) -> UserRead:

    # Ensure the principal is a user
    if principal.kind != "user" or not principal.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a user token")

    return principal.user


# Read a user by ID
@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get a user by unique identifier",
    description="**Retrieve a user by their unique identifier**\n"
    "- `user_id`: The unique identifier of the user to retrieve.",
    response_description="The requested user",
)
async def read_user_by_id(
    user_id: UUID = Path(..., description="Unique user identifier"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = requires_permission(Permissions.USERS_READ),
) -> UserRead:
    return await user_service.read_by_id(user_id=user_id)


# Update a user by ID
@router.patch(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update a user partially",
    description="**Update user fields**\n"
    "- `Full Name`: Update the user's full name.\n"
    "- `Is Active`: Update the user's active status.\n"
    "- `Is Superuser`: Update the user's superuser status.\n"
    "- `Roles`: List of roles assigned to this user. Setting this field will replace all existing roles of the user with the provided list,"
    " and setting an empty list will remove all roles from the user.",
    response_description="Updated user",
)
async def update_user(
    user_id: UUID = Path(..., description="Unique user identifier"),
    payload: UserUpdate = ...,
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = requires_permission(Permissions.USERS_UPDATE),
) -> UserRead:
    return await user_service.update(user_id, payload)


# Change email
@router.put(
    "/email",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Change user email",
    description="**Change the email address of the current user. This will log out the user from all devices.**\n"
    "- `Current Email`: The current email address for verification.\n"
    "- `New Email`: The new email address.\n"
    "- `Current Password`: The current password for verification.",
    response_description="Updated user",
)
async def change_user_email(
    payload: UserChangeEmail = None,
    principal: Principal = Depends(get_current_principal),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    if principal.kind != "user" or not principal.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a user token")

    return await user_service.change_email(principal.user.id, payload)


# Change password
@router.put(
    "/password",
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    description="**Change the password of the current user. This will log out the user from all devices.**\n"
    "- `Old Password`: The current password for verification.\n"
    "- `New Password`: The new password to set.",
    response_description="Updated user",
)
async def change_user_password(
    payload: PasswordChange = None,
    principal: Principal = Depends(get_current_principal),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    if principal.kind != "user" or not principal.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a user token")

    return await user_service.change_password(principal.user.id, payload)


# Add a role to a user
@router.post(
    "/{user_id}/roles/{role_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Add a role to a user",
    description="**Assign a role to a user**\n"
    "- `user_id`: Unique identifier of the user.\n"
    "- `role_id`: Unique identifier of the role to add.",
    response_description="User with the added role",
)
async def add_role_to_user(
    user_id: UUID = Path(..., description="Unique user identifier"),
    role_id: UUID = Path(..., description="Unique role identifier to add"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = requires_permission(Permissions.USERS_UPDATE),
) -> UserRead:
    return await user_service.assign_role(user_id, role_id)


# Remove a role from a user
@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Remove a role from a user",
    description="**Remove the specified role from a user.**\n"
    "- `user_id`: Unique identifier of the user.\n"
    "- `role_id`: Unique identifier of the role to remove.",
    response_description="User with the role removed",
)
async def remove_role_from_user(
    user_id: UUID = Path(..., description="Unique user identifier"),
    role_id: UUID = Path(..., description="Unique role identifier to remove"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = requires_permission(Permissions.USERS_UPDATE),
) -> UserRead:
    return await user_service.remove_role(user_id, role_id)


# Delete a user by ID
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description="**Permanently delete a user account**\n" "- `user_id`: The unique identifier of the user to delete.",
)
async def delete_user(
    user_id: UUID = Path(..., description="Unique user identifier"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserRead = requires_permission(Permissions.USERS_DELETE),
) -> None:
    await user_service.delete(user_id)
