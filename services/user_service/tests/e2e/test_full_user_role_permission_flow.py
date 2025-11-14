import pytest
from uuid import uuid4
from httpx import AsyncClient
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateInDB
from app.core.security import hash_password
from app.core.config import settings

async def _create_admin(db_session, email: str, password: str) -> None:
    repo = UserRepository()
    dto = UserCreateInDB(
        email = email,
        full_name = "E2E Admin Permission",
        hashed_password = hash_password(password),
        is_active = True,
        is_superuser = True,
        require_password_change = False,
    )
    await repo.create(db_session, dto)

@pytest.mark.anyio
async def test_full_flow_user_role_permission(async_client: AsyncClient, db_session, token_headers) -> None:
    
    """
    Enter to exit user flow:
    -  First, create an admin user via repository.
    -  Admin creates permissions and a role with those permissions via API.
    -  Register a new user via API.
    -  Admin assigns the role to the user via API.
    -  User logs in and accesses protected routes via API.
    -  User refreshes token and logs out via API.
    """

    # 1. Create admin user
    admin_email = f"admin_e2e_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    admin_headers = await token_headers(admin_email, admin_password)

    # 2. Admin creates 'CREATE' and 'READ' permissions for users
    perm_create_name = f"users:create"
    perm_read_name = f"users:read"

    # 'Create' permission
    perm_create_resp = await async_client.post(
        f"{settings.route_prefix}/permissions",
        json={"name": perm_create_name, "description": "Can create users"},
        headers = admin_headers,
    )
    assert perm_create_resp.status_code == 201
    perm_create = perm_create_resp.json()

    # 'Read' permission
    perm_read_resp = await async_client.post(
        f"{settings.route_prefix}/permissions",
        json={"name": perm_read_name, "description": "Can read users"},
        headers = admin_headers,
    )
    assert perm_read_resp.status_code == 201
    perm_read = perm_read_resp.json()

    # 3. Admin creates role and assigns the created permissions
    role_name = f"role_users_mgr_{uuid4().hex[:4]}"
    role_resp = await async_client.post(
        f"{settings.route_prefix}/roles",
        json={"name": role_name, "description": "User manager role"},
        headers = admin_headers,
    )
    assert role_resp.status_code == 201
    role = role_resp.json()

    # Assign permissions to role
    assign_perm_create_resp = await async_client.post(
        f"{settings.route_prefix}/roles/{role['id']}/permissions/{perm_create['id']}",
        headers = admin_headers,
    )
    assert assign_perm_create_resp.status_code == 200

    assign_perm_read_resp = await async_client.post(
        f"{settings.route_prefix}/roles/{role['id']}/permissions/{perm_read['id']}",
        headers = admin_headers,
    )
    assert assign_perm_read_resp.status_code == 200

    # 4. Register a new user
    register_payload = {
        "email": f"user_e2e_{uuid4().hex[:6]}@gmail.com",
        "full_name": "Auth Login User",
        "password": "StrongPass1!",
    }
    reg_resp = await async_client.post(f"{settings.route_prefix}/auth", json = register_payload)
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    # 5. Admin assigns the role to the user
    assign_role_resp = await async_client.post(
        f"{settings.route_prefix}/users/{user_id}/roles/{role['id']}",
        headers = admin_headers,
    )
    assert assign_role_resp.status_code == 200

    # 6. User logs in and obtains tokens
    user_login_resp = await async_client.post(
        f"{settings.route_prefix}/auth/login",
        data = {"username": reg_resp.json()["email"], "password": "StrongPass1!"},
    )
    assert user_login_resp.status_code == 200
    user_body = user_login_resp.json()
    user_tokens = user_body["token"]
    user_access_token = user_tokens["access_token"]
    assert "access_token" in user_tokens
    user_refresh_token = user_tokens["refresh_token"]
    assert "refresh_token" in user_tokens
    user_headers = {"Authorization": f"Bearer {user_access_token}"}

    # 7. User now has access to protected routes requiring those permissions
    read_users_resp = await async_client.get(f"{settings.route_prefix}/users", headers = user_headers)
    assert read_users_resp.status_code == 200

    create_other_user_resp = await async_client.post(
        f"{settings.route_prefix}/users",
        json = {
            "email": f"created_by_user_{uuid4().hex[:6]}@gmail.com",
            "full_name": "Created By User",
            "password": "StrongPass1!",
        },
        headers = user_headers,
    )
    assert create_other_user_resp.status_code == 201

    # 8. User refreshes the access token
    refresh_resp = await async_client.post(
        f"{settings.route_prefix}/auth/refresh",
        json = {"refresh_token": user_refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()["token"]
    assert new_tokens["access_token"] != user_access_token

    # 9. User logs out and ensures the refresh token is no longer valid
    logout_resp = await async_client.post(
        f"{settings.route_prefix}/auth/logout",
        json = {"refresh_token": user_refresh_token},
        headers = {"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert logout_resp.status_code == 204

    refresh_again_resp = await async_client.post(
        f"{settings.route_prefix}/auth/refresh",
        json = {"refresh_token": user_refresh_token},
    )
    assert refresh_again_resp.status_code in {400, 401}

@pytest.mark.anyio
async def test_full_flow_user_without_role_cannot_access(async_client: AsyncClient) -> None:
    
    """E2E: user without role should not access protected user management routes."""

    # 1. User registers without any role via API
    email = f"user_e2e_norole_{uuid4().hex[:6]}@gmail.com"
    password = "StrongPass1!"

    reg_resp = await async_client.post(
        f"{settings.route_prefix}/auth",
        json={"email": email, "full_name": "No Role User", "password": password},
    )
    assert reg_resp.status_code == 201

    # 2. User logs in via API
    login_resp = await async_client.post(
        f"{settings.route_prefix}/auth/login",
        data={"username": email, "password": password},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()["token"]
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. User tries to access protected routes
    list_resp = await async_client.get(f"{settings.route_prefix}/users", headers = headers)
    assert list_resp.status_code == 403

    create_resp = await async_client.post(
        f"{settings.route_prefix}/users",
        json = {
            "email": f"created_by_norole_{uuid4().hex[:6]}@gmail.com",
            "full_name": "Created By No Role",
            "password": "StrongPass1!",
        },
        headers = headers,
    )
    assert create_resp.status_code == 403