import pytest
from uuid import uuid4
from httpx import AsyncClient
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateInDB
from app.core.security import hash_password
from app.core.security import verify_password
from app.core.config import settings


async def _create_admin(db_session, email: str, password: str) -> None:
    repo = UserRepository()
    dto = UserCreateInDB(
        email=email,
        full_name="Integration Admin User",
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=True,
        require_password_change=False,
    )
    await repo.create(db_session, dto)


@pytest.mark.anyio
async def test_create_user_by_admin(async_client: AsyncClient, db_session, token_headers):
    """An admin user should be able to create a new user via the API."""

    admin_email = f"admin2_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    payload = {
        "email": f"newuser_{uuid4().hex[:6]}@gmail.com",
        "full_name": "New User",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }

    resp = await async_client.post(f"{settings.route_prefix}/users", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload["email"]


@pytest.mark.anyio
async def test_create_user_unauthenticated(async_client: AsyncClient):
    """Creating a user without authentication should return 401."""

    payload = {
        "email": f"newuser_unauth_{uuid4().hex[:6]}@gmail.com",
        "full_name": "New User Unauth",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }

    resp = await async_client.post(f"{settings.route_prefix}/users", json=payload)
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_read_current_user_profile(async_client: AsyncClient, db_session, token_headers):
    """Fetching the current user's profile should return correct UserReadDetailed data."""

    email = "admin_integ@gmail.com"
    password = "StrongPass1!"

    await _create_admin(db_session, email, password)

    headers = await token_headers(email, password)

    resp = await async_client.get(f"{settings.route_prefix}/users/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email


@pytest.mark.anyio
async def test_read_current_user_profile_unauthenticated(async_client: AsyncClient):
    """Fetching the current user's profile without authentication should return 401."""

    resp = await async_client.get(f"{settings.route_prefix}/users/me")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_read_users_with_filter(async_client: AsyncClient, db_session, token_headers):
    """Retrieving users with email filter should return matching users."""

    admin_email = f"admin3_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    # First, create a target user to filter for
    target_email = f"target_{uuid4().hex[:6]}@gmail.com"
    headers = await token_headers(admin_email, admin_password)

    payload = {
        "email": target_email,
        "full_name": "Target User",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=payload, headers=headers)
    assert create_resp.status_code == 201

    # Now, read users with email filter
    resp = await async_client.get(f"{settings.route_prefix}/users?email={target_email}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(u["email"] == target_email for u in data)


@pytest.mark.anyio
async def test_read_users_with_filter_unauthenticated(async_client: AsyncClient):
    """Listing users with filter without authentication should return 401."""

    target_email = f"target_unauth_{uuid4().hex[:6]}@gmail.com"
    resp = await async_client.get(f"{settings.route_prefix}/users?email={target_email}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_read_user_by_id(async_client: AsyncClient, db_session, token_headers):
    """Retrieving a user by ID should return the correct user."""

    admin_email = f"admin_rid_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    # Create target user via API to read later
    headers = await token_headers(admin_email, admin_password)
    payload = {
        "email": f"uid_{uuid4().hex[:6]}@gmail.com",
        "full_name": "Target ReadById",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Now read user by ID
    resp = await async_client.get(f"{settings.route_prefix}/users/{created['id']}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == created["email"]


@pytest.mark.anyio
async def test_read_user_by_id_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Reading a user by ID without auth should fail with 401."""

    admin_email = f"admin_rid_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    payload = {
        "email": f"uid_noauth_{uuid4().hex[:6]}@gmail.com",
        "full_name": "Target ReadById Noauth",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(
        f"{settings.route_prefix}/users",
        json=payload,
        headers=headers,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.get(f"{settings.route_prefix}/users/{created['id']}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_update_user(async_client: AsyncClient, db_session, token_headers):
    """Update an existing user via the API."""

    admin_email = f"admin_up_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    # Create user to update via API
    headers = await token_headers(admin_email, admin_password)
    create_payload = {
        "email": f"upd_{uuid4().hex[:6]}@gmail.com",
        "full_name": "To Update",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Now update the user
    payload = {"full_name": "Updated Name"}
    resp = await async_client.patch(f"{settings.route_prefix}/users/{created['id']}", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Updated Name"


@pytest.mark.anyio
async def test_update_user_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Updating a user without authentication should return 401."""

    admin_email = f"admin_up_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {
        "email": f"upd_noauth_{uuid4().hex[:6]}@gmail.com",
        "full_name": "To Update Noauth",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(
        f"{settings.route_prefix}/users",
        json=create_payload,
        headers=headers,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()

    payload = {"full_name": "Should Not Update"}
    resp = await async_client.patch(
        f"{settings.route_prefix}/users/{created['id']}",
        json=payload,
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_change_email_and_password(async_client: AsyncClient, db_session, token_headers):
    """A user should be able to change their own email and password via the API."""

    # Create user who will change their own email and password
    email = f"self_{uuid4().hex[:6]}@gmail.com"
    old_password = "OldPass1!"
    new_password = "NewPass1!"
    create_payload = {
        "email": email,
        "full_name": "Self User",
        "password": old_password,
        "is_active": True,
        "is_superuser": False,
    }

    admin_email2 = f"admin_self_{uuid4().hex[:6]}@gmail.com"
    admin_password2 = "StrongPass1!"
    UserCreateInDB(
        email=admin_email2,
        full_name="Tmp Admin",
        hashed_password=hash_password(admin_password2),
        is_active=True,
        is_superuser=True,
        require_password_change=False,
    )
    await _create_admin(db_session, admin_email2, admin_password2)
    admin_headers = await token_headers(admin_email2, admin_password2)
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=create_payload, headers=admin_headers)
    assert create_resp.status_code == 201

    # Change email
    headers = await token_headers(email, old_password)
    new_email = f"self_new_{uuid4().hex[:6]}@gmail.com"
    payload = {"current_email": email, "new_email": new_email, "current_password": old_password}
    resp = await async_client.put(f"{settings.route_prefix}/users/email", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == new_email

    # Change password
    headers2 = await token_headers(new_email, old_password)
    pw_payload = {"old_password": old_password, "new_password": new_password}
    resp2 = await async_client.put(f"{settings.route_prefix}/users/password", json=pw_payload, headers=headers2)
    assert resp2.status_code == 200

    # Verify password stored matches new password
    repo = UserRepository()
    updated = await repo.read_by_email(db_session, new_email)
    assert verify_password(new_password, updated.hashed_password)


@pytest.mark.anyio
async def test_change_email_and_password_unauthenticated(async_client: AsyncClient):
    """Changing email or password without authentication should return 401."""

    email = f"self_unauth_{uuid4().hex[:6]}@gmail.com"

    new_email = f"self_new_unauth_{uuid4().hex[:6]}@gmail.com"
    email_payload = {"current_email": email, "new_email": new_email, "current_password": "OldPass1!"}
    resp_email = await async_client.put(f"{settings.route_prefix}/users/email", json=email_payload)
    assert resp_email.status_code == 401

    pw_payload = {"old_password": "OldPass1!", "new_password": "NewPass1!"}
    resp_pw = await async_client.put(f"{settings.route_prefix}/users/password", json=pw_payload)
    assert resp_pw.status_code == 401


@pytest.mark.anyio
async def test_assign_and_remove_role(async_client: AsyncClient, db_session, token_headers):
    """An admin user should be able to assign and remove roles to/from a user via the API."""

    admin_email = f"admin_role_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    # Create target user
    UserCreateInDB(
        email=f"role_user_{uuid4().hex[:6]}@gmail.com",
        full_name="Role Target",
        hashed_password=hash_password("StrongPass1!"),
        is_active=True,
        is_superuser=False,
        require_password_change=False,
    )
    headers = await token_headers(admin_email, admin_password)
    create_payload = {
        "email": f"role_user_{uuid4().hex[:6]}@gmail.com",
        "full_name": "Role Target",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Create role
    role_payload = {"name": f"r_{uuid4().hex[:6]}", "description": "test role"}
    role_create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=role_payload, headers=headers)
    assert role_create_resp.status_code == 201
    role = role_create_resp.json()

    # Assign role to user
    resp = await async_client.post(f"{settings.route_prefix}/users/{created['id']}/roles/{role['id']}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert any(r["name"] == role["name"] for r in data.get("roles", []))

    # Remove role from user
    resp2 = await async_client.delete(
        f"{settings.route_prefix}/users/{created['id']}/roles/{role['id']}", headers=headers
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert all(r["name"] != role["name"] for r in data2.get("roles", []))


@pytest.mark.anyio
async def test_assign_and_remove_role_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Assigning or removing a role without authentication should return 401."""

    admin_email = f"admin_role_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {
        "email": f"role_user_noauth_{uuid4().hex[:6]}@gmail.com",
        "full_name": "Role Target Noauth",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    role_payload = {"name": f"r_noauth_{uuid4().hex[:6]}", "description": "test role noauth"}
    role_create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=role_payload, headers=headers)
    assert role_create_resp.status_code == 201
    role = role_create_resp.json()

    resp_assign = await async_client.post(f"{settings.route_prefix}/users/{created['id']}/roles/{role['id']}")
    assert resp_assign.status_code == 401

    resp_remove = await async_client.delete(f"{settings.route_prefix}/users/{created['id']}/roles/{role['id']}")
    assert resp_remove.status_code == 401


@pytest.mark.anyio
async def test_delete_user(async_client: AsyncClient, db_session, token_headers):
    """An admin user should be able to delete a user via the API."""

    admin_email = f"admin_del_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    # Create user to delete
    UserCreateInDB(
        email=f"del_{uuid4().hex[:6]}@gmail.com",
        full_name="To Delete",
        hashed_password=hash_password("StrongPass1!"),
        is_active=True,
        is_superuser=False,
        require_password_change=False,
    )
    headers = await token_headers(admin_email, admin_password)
    create_payload = {
        "email": f"del_{uuid4().hex[:6]}@gmail.com",
        "full_name": "To Delete",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Delete the user
    resp = await async_client.delete(f"{settings.route_prefix}/users/{created['id']}", headers=headers)
    assert resp.status_code == 204

    # Confirm deletion
    get_resp = await async_client.get(f"{settings.route_prefix}/users/{created['id']}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_delete_user_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Deleting a user without authentication should return 401."""

    admin_email = f"admin_del_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {
        "email": f"del_noauth_{uuid4().hex[:6]}@gmail.com",
        "full_name": "To Delete Noauth",
        "password": "StrongPass1!",
        "is_active": True,
        "is_superuser": False,
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/users", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.delete(f"{settings.route_prefix}/users/{created['id']}")
    assert resp.status_code == 401
