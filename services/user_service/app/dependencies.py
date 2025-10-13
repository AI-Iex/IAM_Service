from fastapi import Depends
from app.repositories.user import UserRepository
from app.repositories.interfaces import IUserRepository
from app.services.user import UserService
from app.services.interfaces import IUserService

def get_user_repository() -> IUserRepository:
    return UserRepository()

def get_user_service(repo: IUserRepository = Depends(get_user_repository)) -> IUserService:
    return UserService(user_repo=repo)
