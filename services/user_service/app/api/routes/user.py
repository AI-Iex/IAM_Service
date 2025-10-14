from fastapi import APIRouter, Depends, status, Query
from app.schemas.user import UserCreate, UserRead
from app.services.user import UserService
from app.dependencies import get_user_service
from app.api.routes.wrapper import ExceptionHandlingRoute

router = APIRouter(route_class = ExceptionHandlingRoute, prefix = "/users", tags = ["Users"])

# region CREATE

# Create a new user
@router.post("", response_model = UserRead, status_code = status.HTTP_201_CREATED, summary = "Create a new user", response_description = "The created user")
def create_user(payload: UserCreate, user_service: UserService = Depends(get_user_service)):
    user = user_service.create(payload)
    return user

# endregion CREATE

# region READ


# Read users by name (search with pagination)
@router.get(
    "/search",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Get a list of users by name with pagination",
    description="Search for users by their full name (partial match).",
    response_description="List of users matching the name (may be empty)"
)
def read_users_by_name(
    name: str = Query(..., min_length=2, description="Partial or full name to search for"),
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    user_service: UserService = Depends(get_user_service)
) -> list[UserRead]:
    return user_service.read_by_name(name=name, skip=skip, limit=limit)

# Read user by email
@router.get("/by_email", response_model = UserRead, status_code = status.HTTP_200_OK, summary="Get a user by email", response_description="The user with the specified email")
def read_user_by_email(email: str, user_service: UserService = Depends(get_user_service)):
    user = user_service.read_by_email(email)
    return user

# Read a user by ID
@router.get("/{user_id}", response_model = UserRead, status_code = status.HTTP_200_OK, summary="Get a user by ID", response_description="The user with the specified ID")
def read_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    user = user_service.read_by_id(user_id)
    return user

# Read all users with pagination
@router.get("/{skip}/{limit}", response_model=list[UserRead], status_code=200)
def read_all_users_with_pagination(skip: int = 0, limit: int = 100, user_service: UserService = Depends(get_user_service)):
    users = user_service.read_all(skip=skip, limit=limit)
    return users

# Read active users with pagination
@router.get("/active/{skip}/{limit}", response_model=list[UserRead], status_code=200)
def read_active_users_with_pagination(skip: int = 0, limit: int = 100, user_service: UserService = Depends(get_user_service)):
    users = user_service.read_active(skip=skip, limit=limit)
    return users

# Read superusers with pagination
@router.get("/superusers/{skip}/{limit}", response_model=list[UserRead], status_code=200)
def read_superusers_with_pagination(skip: int = 0, limit: int = 100, user_service: UserService = Depends(get_user_service)):
    users = user_service.read_superusers(skip=skip, limit=limit)
    return users

# endregion READ

# region UPDATE

# Update a user by ID
@router.put("/{user_id}", response_model=UserRead, status_code=200)
def update_user(user_id: str, payload: UserCreate, user_service: UserService = Depends(get_user_service)):
    user = user_service.update(user_id, payload)
    return user

# Set user roles
@router.post("/{user_id}/roles", response_model=UserRead, status_code=200)
def set_user_roles(user_id: str, roles: list[str], user_service: UserService = Depends(get_user_service)):
    user = user_service.set_roles(user_id, roles)
    return user

# Update last login
@router.put("/{user_id}/last_login", response_model=UserRead, status_code=200)
def update_last_login(user_id: str, user_service: UserService = Depends(get_user_service)):
    user = user_service.update_last_login(user_id)
    return user

# endregion UPDATE

# region DELETE

# Delete a user by ID
@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, user_service: UserService = Depends(get_user_service)):
    user_service.delete(user_id)
    return

# endregion DELETE