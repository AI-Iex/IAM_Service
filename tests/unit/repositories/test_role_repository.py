import pytest
from app.repositories.role import RoleRepository
from app.repositories.permission import PermissionRepository
from app.schemas.role import RoleCreate, RoleUpdateInDB
from app.schemas.permission import PermissionCreate

def _make_role_dto(name: str, description: str) -> RoleCreate:
	
    '''Creates a RoleCreate DTO for testing.'''

    return RoleCreate(name = name, description = description)

# region CRUD and PERMISSIONS MANAGEMENT

@pytest.mark.anyio
async def test_create_role(db_session):
	
	"""Create a role and verify fields are persisted."""
	
	role_repo = RoleRepository()

	r = await role_repo.create(db_session, _make_role_dto("role-test", "desc"))
	assert r.name == "role-test"
	assert r.description == "desc"

@pytest.mark.anyio
async def test_assign_and_list_permissions(db_session):
	
	"""Assign permissions to a role (single and replace with list) and verify results."""
	
	role_repo = RoleRepository()
	perm_repo = PermissionRepository()

	# create permissions
	p1 = await perm_repo.create(db_session, PermissionCreate(name="perm:one", description="p1"))
	p2 = await perm_repo.create(db_session, PermissionCreate(name="perm:two", description="p2"))

	# create role
	r = await role_repo.create(db_session, _make_role_dto("role-perm", "desc"))

	# assign single permission
	r2 = await role_repo.assign_permission(db_session, r.id, p1.id)
	assert any(p.name == "perm:one" for p in r2.permissions)

	# replace permissions with list
	r3 = await role_repo.assign_list_permissions(db_session, r.id, [p2.id])
	perms = [p.name for p in r3.permissions]
	assert perms == ["perm:two"]

@pytest.mark.anyio
async def test_has_and_remove_permission(db_session):
	
	"""Check has_permission and remove_permission behavior for a role."""
	
	role_repo = RoleRepository()
	perm_repo = PermissionRepository()

	p = await perm_repo.create(db_session, PermissionCreate(name="perm:check", description="p"))
	r = await role_repo.create(db_session, _make_role_dto("role-check", "desc"))

	await role_repo.assign_permission(db_session, r.id, p.id)
	has = await role_repo.has_permission(db_session, r.id, p.id)
	assert has is True

	await role_repo.remove_permission(db_session, r.id, p.id)
	has2 = await role_repo.has_permission(db_session, r.id, p.id)
	assert has2 is False

@pytest.mark.anyio
async def test_update_role_and_delete(db_session):
	
	"""Update a role and then delete it (delete should not raise)."""
	
	role_repo = RoleRepository()

	r = await role_repo.create(db_session, _make_role_dto("role-upd", "desc"))
	upd = RoleUpdateInDB(description="newdesc")
	r2 = await role_repo.update(db_session, r.id, upd)
	assert r2.description == "newdesc"

	# delete (should not raise)
	await role_repo.delete(db_session, r.id)

# endregion CRUD and PERMISSIONS MANAGEMENT

# region FILTERS / READS

@pytest.mark.anyio
async def test_role_filters(db_session):
	
    """Test read_with_filters with name and description filters."""
	
    role_repo = RoleRepository()

    await role_repo.create(db_session, _make_role_dto("alpha", "first"))
    await role_repo.create(db_session, _make_role_dto("beta", "second"))

    res = await role_repo.read_with_filters(db_session, name="alp")
    assert any(x.name == "alpha" for x in res)
	
    des = await role_repo.read_with_filters(db_session, description="second")
    assert any(x.name == "beta" for x in des)
	
    empty_res = await role_repo.read_with_filters(db_session, name="Nonexistent")
    assert len(empty_res) == 0

@pytest.mark.anyio
async def test_read_by_names(db_session):
	
	"""read_by_names should return the roles whose names are in the provided list."""
	
	role_repo = RoleRepository()

	await role_repo.create(db_session, _make_role_dto("alpha", "first"))
	await role_repo.create(db_session, _make_role_dto("beta", "second"))

	res_names = await role_repo.read_by_names(db_session, ["alpha", "beta"]) 
	names = {r.name for r in res_names}
	assert {"alpha","beta"}.issubset(names)

# endregion FILTERS / READS

