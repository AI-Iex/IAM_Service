from fastapi import APIRouter, Depends, status, Query, Path, HTTPException
from typing import List, Optional
from uuid import UUID
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserChangeEmail, PasswordChange
from app.services.user import UserService
from app.dependencies.services import get_user_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix = "/users", tags = ["Users"])

# region CREATE

# Create a new user
@router.post(
    "",   
    response_model = UserRead,
    status_code = status.HTTP_201_CREATED,
    summary = "Create a new user",
    description = "Create a new user with the provided details",
    response_description = "The created user" 
)
async def create_user(
    payload: UserCreate,
    user_service: UserService = Depends(get_user_service)
) -> UserRead:
    return await user_service.create(payload)

# endregion CREATE

# region READ

# Read users with filters
@router.get(
    "",
    response_model = List[UserRead],
    status_code = status.HTTP_200_OK,
    summary = "Get users with filtering and pagination",
    description = "Retrieve users with optional filtering by name, email, status and pagination",
    response_description = "List of users matching criteria"
)
async def read_with_filters(
    name: Optional[str] = Query(None, min_length = 2, description = "Partial name search"),
    email: Optional[str] = Query(None, description = "Exact email match"),
    active: Optional[bool] = Query(None, description = "Filter by active status"),
    is_superuser: Optional[bool] = Query(None, description = "Filter by superuser status"),
    skip: int = Query(0, ge = 0, description = "Number of records to skip (offset)"),
    limit: int = Query(100, ge = 1, le = 100, description = "Maximum records to return"),
    user_service: UserService = Depends(get_user_service)
) -> List[UserRead]:
    return await user_service.read_with_filters(
        name = name, email = email, active = active, 
        is_superuser = is_superuser, skip = skip, limit = limit
    )

# Read a user by ID
@router.get(
        "/{user_id}",
        response_model = UserRead,
        status_code = status.HTTP_200_OK,
        summary = "Get a user by unique identifier",
        description = "Retrieve a user by their unique identifier",
        response_description = "The requested user"
)
async def read_user_by_id(
    user_id: UUID = Path(..., description = "Unique user identifier"),
    user_service: UserService = Depends(get_user_service)
) -> UserRead:
    return await user_service.read_by_id(user_id = user_id)

# endregion READ

# region UPDATE

# Update a user by ID
@router.patch(
    "/{user_id}",
    response_model = UserRead,
    status_code = status.HTTP_200_OK,
    summary = "Update a user partially",
    description = "Update user fields (name, active status, superuser status)",
    response_description = "Updated user"
)
async def update_user(
    user_id: UUID = Path(..., description = "Unique user identifier"),
    payload: UserUpdate = None,
    user_service: UserService = Depends(get_user_service)
) -> UserRead: 
    return await user_service.update(user_id, payload)

# Set user roles
@router.put(
    "/{user_id}/roles",
    response_model = UserRead,
    status_code = status.HTTP_200_OK,
    summary = "Update the user's roles",
    description = "Update the user with the given list of roles",
    response_description = "User with the updated roles"
)
async def set_user_roles(
    user_id: int = Path(..., description = "Unique user identifier"),
    # !Cambiar a recibir una lista de DTOs de Roles? Mirar para mantenerlo desacoplado, hacerlo al final.
    roles: list[str] = Query(..., description = "List of roles to assign"),
    user_service: UserService = Depends(get_user_service)
) -> UserRead:
    return await user_service.set_roles(user_id, roles)

 # !Eliminarlo como ruta y mover funcionalidad a servicio

 # ✅ Change email (UserService)
@router.put(
    "/{user_id}/email",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Change user email"
)
async def change_user_email(
    user_id: UUID = Path(..., description="Unique user identifier"),
    payload: UserChangeEmail = None,
    current_user: UserRead = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserRead:
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return await user_service.change_email(user_id, payload)


# ✅ Change password (UserService)
@router.put(
    "/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password"
)
async def change_user_password(
    user_id: UUID = Path(..., description="Unique user identifier"),
    payload: PasswordChange = None,
    current_user: UserRead = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> None:
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    await user_service.change_password(user_id, payload)


# endregion UPDATE

# region DELETE

# Delete a user by ID
@router.delete(
    "/{user_id}",
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Delete a user",
    description = "Permanently delete a user account",
    response_description = "User successfully deleted"
)
async def delete_user(
        user_id: UUID = Path(..., description = "Unique user identifier"),
        user_service: UserService = Depends(get_user_service)
) -> None:
    await user_service.delete(user_id)
    return None

# endregion DELETE