import pytest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from app.services.permission import PermissionService
from app.core.exceptions import EntityAlreadyExists, NotFoundError
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate


class DummyUoW:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_permission_obj(name: str = "users:read"):
    return SimpleNamespace(id=uuid4(), name=name, description="")


# region CREATE


@pytest.mark.anyio
async def test_create_permission_success():
    """Creating a new permission with a unique name should succeed and return PermissionRead."""

    payload = PermissionCreate(name="users:read", description="desc")

    permission_repo = MagicMock()
    permission_repo.read_with_filters = AsyncMock(return_value=[])
    permission_repo.create = AsyncMock(return_value=make_permission_obj(name=payload.name))

    svc = PermissionService(permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    res = await svc.create(payload)
    assert isinstance(res, PermissionRead)
    assert res.name == "users:read"


@pytest.mark.anyio
async def test_create_permission_duplicate_name_raises():
    """Creating a permission with a duplicate name should raise EntityAlreadyExists."""

    payload = PermissionCreate(name="users:read")

    permission_repo = MagicMock()
    permission_repo.read_with_filters = AsyncMock(return_value=[make_permission_obj(name=payload.name)])

    svc = PermissionService(permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(EntityAlreadyExists):
        await svc.create(payload)


# endregion CREATE

# region READ_BY_ID


@pytest.mark.anyio
async def test_read_by_id_success_and_not_found():
    """Reading a permission by ID should return PermissionRead if found, otherwise raise NotFoundError."""

    perm = make_permission_obj()
    permission_repo = MagicMock()
    permission_repo.read_by_id = AsyncMock(return_value=perm)

    svc = PermissionService(permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    got = await svc.read_by_id(perm.id)
    assert isinstance(got, PermissionRead)
    assert got.name == perm.name

    permission_repo.read_by_id = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.read_by_id(uuid4())


# endregion READ_BY_ID

# region UPDATE


@pytest.mark.anyio
async def test_update_not_found_and_duplicate_name():
    """Updating a permission should raise NotFoundError if not found, or EntityAlreadyExists if name duplicates."""

    existing = make_permission_obj(name="old")

    permission_repo = MagicMock()
    permission_repo.read_by_id = AsyncMock(return_value=None)

    svc = PermissionService(permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.update(uuid4(), PermissionUpdate(name="x"))

    permission_repo.read_by_id = AsyncMock(return_value=existing)
    permission_repo.read_with_filters = AsyncMock(return_value=[make_permission_obj(name="new")])
    svc = PermissionService(permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(EntityAlreadyExists):
        await svc.update(existing.id, PermissionUpdate(name="new"))


# endregion UPDATE

# region DELETE


@pytest.mark.anyio
async def test_delete_permission_not_found_raises():
    """Deleting a permission that does not exist should raise NotFoundError."""

    permission_repo = MagicMock()
    permission_repo.read_by_id = AsyncMock(return_value=None)
    svc = PermissionService(permission_repo=permission_repo, uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.delete(uuid4())


# endregion DELETE
