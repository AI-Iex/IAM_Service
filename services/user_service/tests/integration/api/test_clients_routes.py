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
        full_name = "Integration Admin Client",
        hashed_password = hash_password(password),
        is_active = True,
        is_superuser = True,
        require_password_change = False,
    )
    await repo.create(db_session, dto)

@pytest.mark.anyio
async def test_create_client(async_client: AsyncClient, db_session, token_headers):

    """An admin user should be able to create a new client via the API."""

    admin_email = f"admin_client_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user to create clients
    await _create_admin(db_session, admin_email, admin_password)

    admin_headers = await token_headers(admin_email, admin_password)

    payload = {
        "name": f"client_{uuid4().hex[:6]}",
        "is_active": True,
    }

    # Create client via API using admin credentials
    resp = await async_client.post(f"{settings.route_prefix}/clients", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    # Verify response data
    assert data["name"] == payload["name"]
    assert data["is_active"] is True
    # Client_id and secret should be present in create response
    assert "client_id" in data
    assert "secret" in data

@pytest.mark.anyio
async def test_create_client_unauthenticated(async_client: AsyncClient):

    """Creating a client without authentication should return 401."""

    payload = {
        "name": f"client_unauth_{uuid4().hex[:6]}",
        "is_active": True,
    }

    resp = await async_client.post(f"{settings.route_prefix}/clients", json = payload)
    assert resp.status_code == 401

@pytest.mark.anyio
async def test_read_clients_with_filter(async_client: AsyncClient, db_session, token_headers):

    """Retrieving clients with name filter should return matching clients."""

    admin_email = f"admin_client_list_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user to create clients
    await _create_admin(db_session, admin_email, admin_password)

    admin_headers = await token_headers(admin_email, admin_password)

    # Create a client to search for
    target_name = f"client_filter_{uuid4().hex[:6]}"
    create_payload = {"name": target_name, "is_active": True}
    create_resp = await async_client.post(f"{settings.route_prefix}/clients", json = create_payload, headers = admin_headers)
    assert create_resp.status_code == 201

    # Retrieve clients with name filter using admin credentials
    resp = await async_client.get(f"{settings.route_prefix}/clients?name={target_name}", headers = admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Verify that the created client is in the response
    assert isinstance(data, list)
    assert any(c["name"] == target_name for c in data)

@pytest.mark.anyio
async def test_read_clients_with_filter_unauthenticated(async_client: AsyncClient):

    """Read clients with filter without authentication should return 401."""

    target_name = f"client_filter_unauth_{uuid4().hex[:6]}"
    resp = await async_client.get(f"{settings.route_prefix}/clients?name={target_name}")
    assert resp.status_code == 401

@pytest.mark.anyio
async def test_read_client_by_id(async_client: AsyncClient, db_session, token_headers):

    """Retrieving a client by ID should return the correct client."""

    admin_email = f"admin_client_rid_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user to read client by ID
    await _create_admin(db_session, admin_email, admin_password)

    admin_headers = await token_headers(admin_email, admin_password)

    # Create client 
    create_payload = {"name": f"client_rid_{uuid4().hex[:6]}", "is_active": True}
    create_resp = await async_client.post(f"{settings.route_prefix}/clients", json = create_payload, headers = admin_headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Retrieve client by ID using admin credentials
    resp = await async_client.get(f"{settings.route_prefix}/clients/{created['id']}", headers = admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Verify that the retrieved client matches the created client
    assert data["id"] == created["id"]
    assert data["name"] == created["name"]

@pytest.mark.anyio
async def test_read_client_by_id_unauthenticated(async_client: AsyncClient, db_session, token_headers):

    """Reading a client by ID without auth should fail with 401."""

    admin_email = f"admin_client_rid_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"client_rid_noauth_{uuid4().hex[:6]}", "is_active": True}
    create_resp = await async_client.post(f"{settings.route_prefix}/clients", json = create_payload, headers = headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.get(f"{settings.route_prefix}/clients/{created['id']}")
    assert resp.status_code == 401

@pytest.mark.anyio
async def test_update_client(async_client: AsyncClient, db_session, token_headers):

    """Update an existing client via the API."""

    admin_email = f"admin_client_up_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user to update clients
    await _create_admin(db_session, admin_email, admin_password)

    admin_headers = await token_headers(admin_email, admin_password)

    # Create client to update
    create_payload = {"name": f"client_up_{uuid4().hex[:6]}", "is_active": True}
    create_resp = await async_client.post(f"{settings.route_prefix}/clients", json = create_payload, headers = admin_headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Update client
    update_payload = {"name": "Updated Client Name", "is_active": False}
    resp = await async_client.patch(f"{settings.route_prefix}/clients/{created['id']}", json = update_payload, headers = admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Verify that the client was updated
    assert data["name"] == "Updated Client Name"
    assert data["is_active"] is False

@pytest.mark.anyio
async def test_update_client_unauthenticated(async_client: AsyncClient, db_session, token_headers):

    """Updating a client without authentication should return 401."""

    admin_email = f"admin_client_up_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"client_up_noauth_{uuid4().hex[:6]}", "is_active": True}
    create_resp = await async_client.post(
        f"{settings.route_prefix}/clients",
        json = create_payload,
        headers = headers,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()

    update_payload = {"name": "Updated Client Name Noauth", "is_active": False}
    resp = await async_client.patch(
        f"{settings.route_prefix}/clients/{created['id']}",
        json = update_payload,
    )
    assert resp.status_code == 401

@pytest.mark.anyio
async def test_assign_and_remove_permission_from_client(async_client: AsyncClient, db_session, token_headers):
    
    """Assign and remove a permission to/from a client via the API."""

    admin_email = f"admin_client_perm_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user to assign permissions to clients
    await _create_admin(db_session, admin_email, admin_password)

    admin_headers = await token_headers(admin_email, admin_password)

    # Create client
    create_payload = {"name": f"client_perm_{uuid4().hex[:6]}", "is_active": True}
    create_resp = await async_client.post(f"{settings.route_prefix}/clients", json = create_payload, headers = admin_headers)
    assert create_resp.status_code == 201
    client = create_resp.json()

    # Create a permission via the API 
    perm_payload = {
        "name": f"clients:test_{uuid4().hex[:6]}",
        "description": "Test permission for client assignment",
    }
    perm_resp = await async_client.post(f"{settings.route_prefix}/permissions", json = perm_payload, headers = admin_headers)
    assert perm_resp.status_code == 201
    permission = perm_resp.json()

    # Assign permission via the API
    resp = await async_client.post(
        f"{settings.route_prefix}/clients/{client['id']}/permissions/{permission['id']}",
        headers = admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any(p["id"] == permission["id"] for p in data.get("permissions", []))

    # Remove permission via the API
    resp2 = await async_client.delete(
        f"{settings.route_prefix}/clients/{client['id']}/permissions/{permission['id']}",
        headers = admin_headers,
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert all(p["id"] != permission["id"] for p in data2.get("permissions", []))

@pytest.mark.anyio
async def test_delete_client(async_client: AsyncClient, db_session, token_headers):
    
    """An admin user should be able to delete a client via the API."""

    admin_email = f"admin_client_del_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    # Create admin user to delete clients
    await _create_admin(db_session, admin_email, admin_password)

    admin_headers = await token_headers(admin_email, admin_password)

    # Create client to delete
    create_payload = {"name": f"client_del_{uuid4().hex[:6]}", "is_active": True}
    create_resp = await async_client.post(f"{settings.route_prefix}/clients", json = create_payload, headers = admin_headers)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Delete client via API using admin credentials
    resp = await async_client.delete(f"{settings.route_prefix}/clients/{created['id']}", headers = admin_headers)
    assert resp.status_code == 204

    # Confirm deletion
    get_resp = await async_client.get(f"{settings.route_prefix}/clients/{created['id']}", headers = admin_headers)
    assert get_resp.status_code == 404

@pytest.mark.anyio
async def test_delete_client_unauthenticated(async_client: AsyncClient, db_session, token_headers):

    """Deleting a client without authentication should return 401."""

    admin_email = f"admin_client_del_noauth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    await _create_admin(db_session, admin_email, admin_password)

    headers = await token_headers(admin_email, admin_password)

    create_payload = {"name": f"client_del_noauth_{uuid4().hex[:6]}", "is_active": True}
    create_resp = await async_client.post(
        f"{settings.route_prefix}/clients",
        json = create_payload,
        headers = headers,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()

    resp = await async_client.delete(f"{settings.route_prefix}/clients/{created['id']}")
    assert resp.status_code == 401
