from fastapi import Depends

from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.role import RoleRepository
from app.repositories.client import ClientRepository
from app.repositories.permission import PermissionRepository
from app.repositories.auth import AuthRepository
from app.repositories.health import HealthRepository

from app.repositories.interfaces.user import IUserRepository
from app.repositories.interfaces.refresh_token import IRefreshTokenRepository
from app.repositories.interfaces.role import IRoleRepository
from app.repositories.interfaces.client import IClientRepository
from app.repositories.interfaces.permission import IPermissionRepository
from app.repositories.interfaces.auth import IAuthRepository
from app.repositories.interfaces.health import IHealthRepository

from app.services.user import UserService
from app.services.auth import AuthService
from app.services.role import RoleService
from app.services.health import HealthService
from app.services.permission import PermissionService
from app.services.client import ClientService

from app.services.interfaces.user import IUserService
from app.services.interfaces.auth import IAuthService
from app.services.interfaces.role import IRoleService
from app.services.interfaces.health import IHealthService
from app.services.interfaces.permission import IPermissionService
from app.services.interfaces.client import IClientService

from app.db.interfaces.unit_of_work import IUnitOfWork
from app.db.unit_of_work import get_uow_factory, UnitOfWorkFactory


# region REPOSITORIES


# User repository
def get_user_repository() -> IUserRepository:
    """Get user repository instance."""
    return UserRepository()


# Role repository
def get_role_repository() -> IRoleRepository:
    """Get role repository instance."""
    return RoleRepository()


# Refresh token repository
def get_refresh_token_repository() -> IRefreshTokenRepository:
    """Get refresh token repository instance."""
    return RefreshTokenRepository()


# Auth repository
def get_auth_repository() -> IAuthRepository:
    """Get auth repository instance."""
    return AuthRepository()


# Client repository
def get_client_repository() -> IClientRepository:
    """Get client repository instance."""
    return ClientRepository()


# Permission repository
def get_permission_repository() -> IPermissionRepository:
    """Get permission repository instance."""
    return PermissionRepository()


# Health repository
def get_health_repository() -> IHealthRepository:
    """Get health repository instance."""
    return HealthRepository()


# endregion REPOSITORIES

# region SERVICES


# Permission service
def get_permission_service(
    repo: IPermissionRepository = Depends(get_permission_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IPermissionService:
    """Get permission service instance."""
    return PermissionService(permission_repo=repo, uow_factory=uow_factory)


# Role service
def get_role_service(
    repo: IRoleRepository = Depends(get_role_repository),
    permission_repo: IPermissionRepository = Depends(get_permission_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IRoleService:
    """Get role service instance."""
    return RoleService(role_repo=repo, permission_repo=permission_repo, uow_factory=uow_factory)


# User service
def get_user_service(
    repo: IUserRepository = Depends(get_user_repository),
    role_repo: IRoleRepository = Depends(get_role_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IUserService:
    """Get user service instance."""
    return UserService(user_repo=repo, role_repo=role_repo, uow_factory=uow_factory)


# Auth service
def get_auth_service(
    repo: IRefreshTokenRepository = Depends(get_refresh_token_repository),
    user_repo: IUserRepository = Depends(get_user_repository),
    client_repo: IClientRepository = Depends(get_client_repository),
    auth_repo: IAuthRepository = Depends(get_auth_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IAuthService:
    """Get auth service instance."""
    return AuthService(
        user_repo=user_repo,
        refresh_token_repo=repo,
        client_repo=client_repo,
        auth_repo=auth_repo,
        uow_factory=uow_factory,
    )


# Health service
def get_health_service(
    repo: IHealthRepository = Depends(get_health_repository), uow_factory: UnitOfWorkFactory = Depends(get_uow_factory)
) -> IHealthService:
    """Get health service instance."""
    return HealthService(health_repo=repo, uow_factory=uow_factory)


# Client service
def get_client_service(
    client_repo: ClientRepository = Depends(get_client_repository),
    permission_repo: IPermissionRepository = Depends(get_permission_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IClientService:
    """Get client service instance."""
    return ClientService(client_repo=client_repo, permission_repo=permission_repo, uow_factory=uow_factory)


# endregion SERVICES
