import pytest
from uuid import uuid4
from app.repositories.auth import AuthRepository
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.repositories.client import ClientRepository
from app.repositories.permission import PermissionRepository
from app.core.security import hash_password
from app.schemas.user import UserCreateInDB
from app.schemas.role import RoleCreate
from app.schemas.permission import PermissionCreate
from app.schemas.client import ClientCreateInDB


@pytest.mark.anyio
async def test_get_user_for_auth_and_client(db_session):
    """AuthRepository.get_user_for_auth should return user with roles and permissions loaded."""

    user_repo = UserRepository()
    role_repo = RoleRepository()
    perm_repo = PermissionRepository()
    auth_repo = AuthRepository()

    # Create permission and role
    p = await perm_repo.create(db_session, PermissionCreate(name="u:read", description=""))
    r = await role_repo.create(db_session, RoleCreate(name="r1", description=""))
    # Assign permission to role
    await role_repo.assign_permission(db_session, r.id, p.id)

    # Create user
    dto = UserCreateInDB(
        email="authrepo_emailcheck@example.com",
        full_name="authrepo_name",
        hashed_password=hash_password("pw"),
        is_active=True,
        is_superuser=False,
        require_password_change=False,
    )
    u = await user_repo.create(db_session, dto)

    # Assign role to user
    await user_repo.assign_role(db_session, u.id, r.id)

    user_auth = await auth_repo.get_user_for_auth(db_session, u.id)
    assert user_auth is not None
    # Roles and permissions should be loaded
    assert any(role.name == "r1" for role in user_auth.roles)


@pytest.mark.anyio
async def test_get_client_for_auth(db_session):
    """AuthRepository.get_client_for_auth should return client by id."""

    client_repo = ClientRepository()
    auth_repo = AuthRepository()

    dto = ClientCreateInDB(name="authcli", is_active=True, secret_hashed="s", client_id=str(uuid4()))
    c = await client_repo.create(db_session, dto)

    auth_client = await auth_repo.get_client_for_auth(db_session, c.id)
    assert auth_client is not None and auth_client.id == c.id
