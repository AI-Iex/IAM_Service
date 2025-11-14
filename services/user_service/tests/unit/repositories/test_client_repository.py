import pytest
from uuid import uuid4
from app.repositories.client import ClientRepository
from app.repositories.permission import PermissionRepository
from app.schemas.client import ClientCreateInDB
from app.schemas.permission import PermissionCreate


def _make_client_dto(name: str) -> ClientCreateInDB:
	
	"""Helper to build a ClientCreateInDB DTO for tests."""
	
	return ClientCreateInDB(name = name, is_active = True, secret_hashed = "sh", client_id = uuid4())

# region CRUD

@pytest.mark.anyio
async def test_create_client(db_session):
	
	"""Create a client and verify basic fields are persisted."""
	
	client_repo = ClientRepository()

	dto = _make_client_dto("cli1")
	c = await client_repo.create(db_session, dto)
	assert c.name == "cli1"

@pytest.mark.anyio
async def test_assign_permission_to_client(db_session):
	
	"""Assign a permission to a client and verify it appears in permissions."""
	
	client_repo = ClientRepository()
	perm_repo = PermissionRepository()

	p = await perm_repo.create(db_session, PermissionCreate(name="clients:astes", description="desc"))
	dto = _make_client_dto("cli-perm")
	c = await client_repo.create(db_session, dto)

	c2 = await client_repo.assign_permission(db_session, c.id, p.id)
	assert any(pp.name == "clients:astes" for pp in c2.permissions)

@pytest.mark.anyio
async def test_remove_permission_from_client(db_session):
	
	"""Remove a permission from a client and verify it is removed."""
	
	client_repo = ClientRepository()
	perm_repo = PermissionRepository()

	p = await perm_repo.create(db_session, PermissionCreate(name="clients:test", description="desc"))
	dto = _make_client_dto("cli-rem")
	c = await client_repo.create(db_session, dto)

	await client_repo.assign_permission(db_session, c.id, p.id)
	c3 = await client_repo.remove_permission(db_session, c.id, p.id)
	assert all(pp.name != "clients:test" for pp in c3.permissions)

@pytest.mark.anyio
async def test_delete_client(db_session):
	
	"""Delete a client and verify it is gone."""
	
	client_repo = ClientRepository()

	dto = _make_client_dto("cli-del")
	c = await client_repo.create(db_session, dto)
	await client_repo.delete(db_session, c.id)

# endregion CRUD

# region READ

@pytest.mark.anyio
async def test_client_read_by_id_and_filters(db_session):
	
    """Read client by id and via read_with_filters by partial name."""

    client_repo = ClientRepository()
    perm_repo = PermissionRepository()

    await perm_repo.create(db_session, PermissionCreate(name="clients:list", description="desc"))

    dto = _make_client_dto("cli-filter")
    c = await client_repo.create(db_session, dto)

    # read_by_id
    c_read = await client_repo.read_by_id(db_session, c.id)
    assert c_read is not None and c_read.id == c.id

    # read_with_filters by name
    res = await client_repo.read_with_filters(db_session, name="cli-")
    assert any(x.id == c.id for x in res)

    # read_with_filters by is_active
    active = await client_repo.read_with_filters(db_session, is_active=True)
    assert any(x.id == c.id for x in active)
	
    # read_with_filters with no matches
    empty = await client_repo.read_with_filters(db_session, name="Nonexistent92829128")
    assert len(empty) == 0

# endregion READ

