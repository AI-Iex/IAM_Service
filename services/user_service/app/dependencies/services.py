from fastapi import Depends
from app.repositories.user import UserRepository
from app.repositories.auth import AuthRepository
from app.repositories.client import ClientRepository
from app.repositories.interfaces.user import IUserRepository
from app.repositories.interfaces.auth import IAuthRepository
from app.services.user import UserService
from app.services.auth import AuthService
from app.services.interfaces.user import IUserService
from app.services.interfaces.auth import IAuthService


# User repository
def get_user_repository() -> IUserRepository:
    ''' Get user repository instance '''
    return UserRepository()


# Auth repository
def get_auth_repository() -> IAuthRepository:
    ''' Get auth repository instance '''
    return AuthRepository()


# Client repository
def get_client_repository() -> ClientRepository:
    ''' Get client repository instance '''
    return ClientRepository()


# User service
def get_user_service(
    repo: IUserRepository = Depends(get_user_repository)
) -> IUserService:
    ''' Get user service instance '''
    return UserService(user_repo = repo)


# Auth service
def get_auth_service(
    repo: IAuthRepository = Depends(get_auth_repository),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> IAuthService:
    ''' Get auth service instance '''
    return AuthService(user_repo=user_repo, auth_repo=repo)
