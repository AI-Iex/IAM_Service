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
        email=email,
        full_name="Integration Admin Role",
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=True,
        require_password_change=False,
    )
    await repo.create(db_session, dto)


@pytest.mark.anyio
async def test_create_role(async_client: AsyncClient, db_session, token_headers):
    """Admin user should be able to create a new role via the API."""

    admin_email = f"admin_role_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    payload = {
        "name": f"role_{uuid4().hex[:6]}",
        "description": "Test role",
    }

    resp = await async_client.post(f"{settings.route_prefix}/roles", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == payload["name"]


@pytest.mark.anyio
async def test_create_role_unauthenticated(async_client: AsyncClient):
    """Creating a role without authentication should return 401."""

    payload = {"name": f"role_unauth_{uuid4().hex[:6]}", "description": "Should not be created"}

    resp = await async_client.post(f"{settings.route_prefix}/roles", json=payload)
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_read_roles_with_filter(async_client: AsyncClient, db_session, token_headers):
    """Retrieving roles with name filter should return matching roles."""

    admin_email = f"admin_role_list_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    target_name = f"role_filter_{uuid4().hex[:6]}"
    create_payload = {"name": target_name, "description": "Role to filter"}
    create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=create_payload, headers=headers)
    assert create_resp.status_code == 201

    resp = await async_client.get(f"{settings.route_prefix}/roles?name={target_name}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(r["name"] == target_name for r in data)


@pytest.mark.anyio
async def test_read_roles_unauthenticated(async_client: AsyncClient):
    """Listing roles without authentication should return 401."""

    resp = await async_client.get(f"{settings.route_prefix}/roles")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_read_role_by_id(async_client: AsyncClient, db_session, token_headers):
    """Retrieving a role by ID should return the correct role."""

    admin_email = f"admin_role_rid_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"role_rid_{uuid4().hex[:6]}", "description": "Role RID"}
    create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.get(f"{settings.route_prefix}/roles/{created['id']}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created["id"]
    assert data["name"] == created["name"]


@pytest.mark.anyio
async def test_read_role_by_id_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Reading a role by ID without auth should fail with 401."""

    admin_email = f"admin_role_rid_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"role_rid_noauth_{uuid4().hex[:6]}", "description": "Role RID noauth"}
    create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.get(f"{settings.route_prefix}/roles/{created['id']}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_update_role(async_client: AsyncClient, db_session, token_headers):
    """Update an existing role via the API."""

    admin_email = f"admin_role_up_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"role_up_{uuid4().hex[:6]}", "description": "Role to update"}
    create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    update_payload = {"description": "Updated role description"}
    resp = await async_client.patch(
        f"{settings.route_prefix}/roles/{created['id']}", json=update_payload, headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Updated role description"


@pytest.mark.anyio
async def test_update_role_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Updating a role without authentication should return 401."""

    admin_email = f"admin_role_up_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {
        "name": f"role_up_noauth_{uuid4().hex[:6]}",
        "description": "Role to update noauth",
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    update_payload = {"description": "Should not be updated"}
    resp = await async_client.patch(f"{settings.route_prefix}/roles/{created['id']}", json=update_payload)
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_delete_role(async_client: AsyncClient, db_session, token_headers):
    """Admin user should be able to delete a role via the API."""

    admin_email = f"admin_role_del_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"role_del_{uuid4().hex[:6]}", "description": "Role to delete"}
    create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.delete(f"{settings.route_prefix}/roles/{created['id']}", headers=headers)
    assert resp.status_code == 204

    get_resp = await async_client.get(f"{settings.route_prefix}/roles/{created['id']}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_delete_role_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Deleting a role without authentication should return 401."""

    admin_email = f"admin_role_del_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"role_del_noauth_{uuid4().hex[:6]}", "description": "Role to delete noauth"}
    create_resp = await async_client.post(f"{settings.route_prefix}/roles", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.delete(f"{settings.route_prefix}/roles/{created['id']}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_assign_and_remove_permission_from_role(async_client: AsyncClient, db_session, token_headers):
    """Assign a permission to a role and then remove it via API."""

    admin_email = f"admin_role_perm_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    # Create role
    role_payload = {
        "name": f"role_perm_{uuid4().hex[:6]}",
        "description": "Role for permissions",
    }
    role_resp = await async_client.post(f"{settings.route_prefix}/roles", json=role_payload, headers=headers)
    assert role_resp.status_code == 201
    role = role_resp.json()

    # Create permission
    perm_payload = {
        "name": f"perm_{uuid4().hex[:6]}",
        "description": "Permission for role",
    }
    perm_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=perm_payload, headers=headers)
    assert perm_resp.status_code == 201
    perm = perm_resp.json()

    # Assign permission to role
    assign_resp = await async_client.post(
        f"{settings.route_prefix}/roles/{role['id']}/permissions/{perm['id']}",
        headers=headers,
    )
    assert assign_resp.status_code in (200, 204)

    # Verify role has the permission
    role_detail = await async_client.get(f"{settings.route_prefix}/roles/{role['id']}", headers=headers)
    assert role_detail.status_code == 200
    role_data = role_detail.json()
    if "permissions" in role_data:
        assert any(p["id"] == perm["id"] for p in role_data["permissions"])

    # Remove permission from role
    remove_resp = await async_client.delete(
        f"{settings.route_prefix}/roles/{role['id']}/permissions/{perm['id']}",
        headers=headers,
    )
    assert remove_resp.status_code in (200, 204)

    # Verify it's no longer there
    role_detail_after = await async_client.get(f"{settings.route_prefix}/roles/{role['id']}", headers=headers)
    assert role_detail_after.status_code == 200
    role_after = role_detail_after.json()
    if "permissions" in role_after:
        assert all(p["id"] != perm["id"] for p in role_after["permissions"])
