import pytest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from app.services.role import RoleService
from app.core.exceptions import EntityAlreadyExists, NotFoundError, DomainError
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate


class DummyUoW:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_permission(name: str = "users:read"):
    return SimpleNamespace(id=uuid4(), name=name, description="")


def make_role_obj(name: str = "admin"):
    return SimpleNamespace(id=uuid4(), name=name, description="", permissions=[])


# region CREATE


@pytest.mark.anyio
async def test_create_role_success():
    """Creating a new role with a unique name should succeed and return RoleRead."""

    payload = RoleCreate(name="admin", permissions=[{"name": "users:read"}])

    role_repo = MagicMock()
    role_repo.read_with_filters = AsyncMock(return_value=[])
    role_repo.create = AsyncMock(return_value=make_role_obj(name=payload.name))
    role_repo.assign_list_permissions = AsyncMock(return_value=make_role_obj(name=payload.name))

    permission_repo = MagicMock()
    permission_repo.read_by_names = AsyncMock(return_value=[make_permission(name="users:read")])

    svc = RoleService(role_repo=role_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    res = await svc.create(payload)
    assert isinstance(res, RoleRead)
    assert res.name == "admin"


@pytest.mark.anyio
async def test_create_role_duplicate_name_raises():
    payload = RoleCreate(name="admin")

    role_repo = MagicMock()
    role_repo.read_with_filters = AsyncMock(return_value=[make_role_obj(name=payload.name)])

    svc = RoleService(role_repo=role_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(EntityAlreadyExists):
        await svc.create(payload)


# endregion CREATE

# region READ_BY_ID


@pytest.mark.anyio
async def test_read_by_id_success_and_not_found():
    """Reading a role by ID should return RoleRead if found, otherwise raise NotFoundError."""

    role = make_role_obj()

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=role)

    svc = RoleService(role_repo=role_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    got = await svc.read_by_id(role.id)
    assert isinstance(got, RoleRead)
    assert got.name == role.name

    role_repo.read_by_id = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.read_by_id(uuid4())


# endregion READ_BY_ID

# region READ_WITH_FILTERS


@pytest.mark.anyio
async def test_read_with_filters_returns_list():
    """Reading roles with filters should return a list of RoleRead."""

    roles = [make_role_obj(name="r1"), make_role_obj(name="r2")]

    role_repo = MagicMock()
    role_repo.read_with_filters = AsyncMock(return_value=roles)

    svc = RoleService(role_repo=role_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    out = await svc.read_with_filters(name="r")
    assert isinstance(out, list)
    assert len(out) == 2


# endregion READ_WITH_FILTERS

# region UPDATE


@pytest.mark.anyio
async def test_update_role_not_found_and_duplicate_name():
    """Updating a role should raise NotFoundError if not found, or EntityAlreadyExists if name duplicates."""

    existing = make_role_obj(name="old")

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=None)

    svc = RoleService(role_repo=role_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.update(uuid4(), RoleUpdate(name="new"))

    # duplicate name case
    role_repo.read_by_id = AsyncMock(return_value=existing)
    role_repo.read_with_filters = AsyncMock(return_value=[make_role_obj(name="new")])
    svc = RoleService(role_repo=role_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    with pytest.raises(EntityAlreadyExists):
        await svc.update(existing.id, RoleUpdate(name="new"))


@pytest.mark.anyio
async def test_update_permissions_missing_permission_raises():
    """Updating a role with non-existent permissions should raise NotFoundError."""

    existing = make_role_obj()

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=existing)
    role_repo.update = AsyncMock(return_value=existing)

    permission_repo = MagicMock()
    permission_repo.read_by_names = AsyncMock(return_value=[])

    svc = RoleService(role_repo=role_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    payload = RoleUpdate(permissions=[{"name": "missing"}])
    with pytest.raises(NotFoundError):
        await svc.update(existing.id, payload)


# endregion UPDATE

# region ASSIGN/REMOVE PERMISSION


@pytest.mark.anyio
async def test_assign_permission_errors_and_remove_errors():
    """Assigning/removing permissions to/from roles should raise errors for not found or already assigned/not assigned cases."""

    # assign: role not found
    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=None)
    svc = RoleService(role_repo=role_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.assign_permission(uuid4(), uuid4())

    # assign: permission not found
    role = make_role_obj()
    role_repo.read_by_id = AsyncMock(return_value=role)
    permission_repo = MagicMock()
    permission_repo.read_by_id = AsyncMock(return_value=None)
    svc = RoleService(role_repo=role_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.assign_permission(role.id, uuid4())

    # assign: already has
    role_repo.has_permission = AsyncMock(return_value=True)
    permission_repo.read_by_id = AsyncMock(return_value=make_permission())
    svc = RoleService(role_repo=role_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(EntityAlreadyExists):
        await svc.assign_permission(role.id, uuid4())

    # remove: role not found
    role_repo.read_by_id = AsyncMock(return_value=None)
    svc = RoleService(role_repo=role_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.remove_permission(uuid4(), uuid4())

    # remove: permission not found
    role_repo.read_by_id = AsyncMock(return_value=role)
    permission_repo.read_by_id = AsyncMock(return_value=None)
    svc = RoleService(role_repo=role_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.remove_permission(role.id, uuid4())

    # remove: not assigned
    permission_repo.read_by_id = AsyncMock(return_value=make_permission())
    role_repo.has_permission = AsyncMock(return_value=False)
    svc = RoleService(role_repo=role_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(EntityAlreadyExists):
        await svc.remove_permission(role.id, uuid4())


# endregion ASSIGN/REMOVE PERMISSION

# region DELETE


@pytest.mark.anyio
async def test_delete_role_not_found_raises():
    """Deleting a role that does not exist should raise NotFoundError."""

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=None)
    svc = RoleService(role_repo=role_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.delete(uuid4())


# endregion DELETE
