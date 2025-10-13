from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserRead
from app.services.user import UserService
from app.dependencies import get_user_service
from app.api.routes.wrapper import ExceptionHandlingRoute

router = APIRouter(route_class=ExceptionHandlingRoute)

# region CREATE
@router.post("/users/create", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, user_service: UserService = Depends(get_user_service)):
    user = user_service.create(payload)
    return user

# endregion CREATE

# region READ
@router.post("/users/read/{user_id}", response_model=UserRead, status_code=200)
def read_user(user_id: str, user_service: UserService = Depends(get_user_service)):
    user = user_service.read(user_id)
    return user

# endregion READ