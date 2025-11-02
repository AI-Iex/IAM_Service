from fastapi import Depends
from app.repositories.user import UserRepository
from app.repositories.auth import AuthRepository
from app.repositories.role import RoleRepository
from app.repositories.client import ClientRepository
from app.repositories.permission import PermissionRepository
from app.repositories.interfaces.user import IUserRepository
from app.repositories.interfaces.auth import IAuthRepository
from app.repositories.interfaces.role import IRoleRepository
from app.repositories.interfaces.permission import IPermissionRepository
from app.services.user import UserService
from app.services.auth import AuthService
from app.services.role import RoleService
from app.services.permission import PermissionService
from app.services.interfaces.user import IUserService
from app.services.interfaces.auth import IAuthService
from app.services.interfaces.role import IRoleService
from app.services.interfaces.permission import IPermissionService
from app.services.health import HealthService
from app.services.interfaces.health import IHealthService
from app.repositories.interfaces.health import IHealthRepository
from app.repositories.health import HealthRepository


# User repository
def get_user_repository() -> IUserRepository:
    ''' Get user repository instance '''
    return UserRepository()


# Role repository
def get_role_repository() -> IRoleRepository:
    ''' Get role repository instance '''
    return RoleRepository()


# Auth repository
def get_auth_repository() -> IAuthRepository:
    ''' Get auth repository instance '''
    return AuthRepository()


# Client repository
def get_client_repository() -> ClientRepository:
    ''' Get client repository instance '''
    return ClientRepository()


# Permission repository
def get_permission_repository() -> IPermissionRepository:
    ''' Get permission repository instance '''
    return PermissionRepository()


# Health repository
def get_health_repository() -> IHealthRepository:
    """Get health repository instance"""
    return HealthRepository()


# Permission service
def get_permission_service(
    repo: IPermissionRepository = Depends(get_permission_repository)
) -> IPermissionService:
    ''' Get permission service instance '''
    return PermissionService(permission_repo = repo)


# Role service
def get_role_service(
    repo: IRoleRepository = Depends(get_role_repository),
    permission_repo: IPermissionRepository = Depends(get_permission_repository)
) -> IRoleService:
    ''' Get role service instance '''
    return RoleService(role_repo = repo, permission_repo = permission_repo)


# User service
def get_user_service(
    repo: IUserRepository = Depends(get_user_repository),
    role_repo: IRoleRepository = Depends(get_role_repository)
) -> IUserService:
    ''' Get user service instance '''
    return UserService(user_repo = repo, role_repo = role_repo)

# Auth service
def get_auth_service(
    repo: IAuthRepository = Depends(get_auth_repository),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> IAuthService:
    ''' Get auth service instance '''
    return AuthService(user_repo = user_repo, auth_repo = repo)


# Health service
def get_health_service(
    repo: IHealthRepository = Depends(get_health_repository)
) -> IHealthService:
    """Get health service instance"""
    return HealthService(health_repo=repo)