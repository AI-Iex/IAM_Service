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
        full_name="Integration Admin Permission",
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=True,
        require_password_change=False,
    )
    await repo.create(db_session, dto)


@pytest.mark.anyio
async def test_create_permission(async_client: AsyncClient, db_session, token_headers):
    """Admin user should be able to create a new permission via the API."""

    admin_email = f"admin_perm_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    payload = {
        "name": f"perm_{uuid4().hex[:6]}",
        "description": "Test permission",
    }

    # Create permission via API using admin credentials
    resp = await async_client.post(f"{settings.route_prefix}/permissions", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == payload["name"]


@pytest.mark.anyio
async def test_create_permission_unauthenticated(async_client: AsyncClient):
    """Creating a permission without authentication should return 401."""

    payload = {
        "name": f"perm_unauth_{uuid4().hex[:6]}",
        "description": "Should not be created",
    }

    resp = await async_client.post(f"{settings.route_prefix}/permissions", json=payload)
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_read_permissions_with_filter(async_client: AsyncClient, db_session, token_headers):
    """Retrieving permissions with name filter should return matching permissions."""

    admin_email = f"admin_perm_list_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    # Create permission via API using admin credentials
    target_name = f"perm_filter_{uuid4().hex[:6]}"
    create_payload = {"name": target_name, "description": "Permission to filter"}
    create_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=create_payload, headers=headers)
    assert create_resp.status_code == 201

    # Now read permissions with filter
    resp = await async_client.get(f"{settings.route_prefix}/permissions?name={target_name}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(p["name"] == target_name for p in data)


@pytest.mark.anyio
async def test_read_permissions_unauthenticated(async_client: AsyncClient):
    """Listing permissions without authentication should return 401."""

    resp = await async_client.get(f"{settings.route_prefix}/permissions")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_read_permission_by_id(async_client: AsyncClient, db_session, token_headers):
    """Retrieving a permission by ID should return the correct permission."""

    admin_email = f"admin_perm_rid_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    # Create permission via API using admin credentials
    create_payload = {"name": f"perm_rid_{uuid4().hex[:6]}", "description": "Permission RID"}
    create_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Retrieve permission by ID using admin credentials
    resp = await async_client.get(f"{settings.route_prefix}/permissions/{created['id']}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created["id"]
    assert data["name"] == created["name"]


@pytest.mark.anyio
async def test_read_permission_by_id_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Reading a permission by ID without auth should fail with 401."""

    admin_email = f"admin_perm_rid_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {
        "name": f"perm_rid_noauth_{uuid4().hex[:6]}",
        "description": "Permission RID noauth",
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Now try to read it without headers
    resp = await async_client.get(f"{settings.route_prefix}/permissions/{created['id']}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_update_permission(async_client: AsyncClient, db_session, token_headers):
    """Update an existing permission via the API."""

    admin_email = f"admin_perm_up_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    # Create a permission with admin first
    create_payload = {"name": f"perm_up_{uuid4().hex[:6]}", "description": "Permission to update"}
    create_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Update permission
    update_payload = {"description": "Updated permission description"}
    resp = await async_client.patch(
        f"{settings.route_prefix}/permissions/{created['id']}",
        json=update_payload,
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Updated permission description"


@pytest.mark.anyio
async def test_update_permission_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Updating a permission without authentication should return 401."""

    admin_email = f"admin_perm_up_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {
        "name": f"perm_up_noauth_{uuid4().hex[:6]}",
        "description": "Permission to update noauth",
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    update_payload = {"description": "Should not be updated"}
    resp = await async_client.patch(
        f"{settings.route_prefix}/permissions/{created['id']}",
        json=update_payload,
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_delete_permission(async_client: AsyncClient, db_session, token_headers):
    """Admin user should be able to delete a permission via the API."""

    admin_email = f"admin_perm_del_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    # Create a permission with admin first
    create_payload = {"name": f"perm_del_{uuid4().hex[:6]}", "description": "Permission to delete"}
    create_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Delete permission
    resp = await async_client.delete(f"{settings.route_prefix}/permissions/{created['id']}", headers=headers)
    assert resp.status_code == 204

    # Verify deletion
    get_resp = await async_client.get(f"{settings.route_prefix}/permissions/{created['id']}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_delete_permission_unauthenticated(async_client: AsyncClient, db_session, token_headers):
    """Deleting a permission without authentication should return 401."""

    admin_email = f"admin_perm_del_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"
    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {
        "name": f"perm_del_noauth_{uuid4().hex[:6]}",
        "description": "Permission to delete noauth",
    }
    create_resp = await async_client.post(f"{settings.route_prefix}/permissions", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Try to delete without headers
    resp = await async_client.delete(f"{settings.route_prefix}/permissions/{created['id']}")
    assert resp.status_code == 401
