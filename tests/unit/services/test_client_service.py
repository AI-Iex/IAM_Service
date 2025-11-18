import pytest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from app.services.client import ClientService
from app.core.exceptions import EntityAlreadyExists, DomainError, NotFoundError
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.core.security import hash_password


class DummyUoW:
    """A minimal async context manager to stand in for UnitOfWork in tests."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_client_obj(name: str = "My Client"):
    """Return a simple namespace that mimics the attributes expected by client schemas."""

    return SimpleNamespace(
        id=uuid4(),
        client_id=uuid4(),
        name=name,
        secret_hashed=hash_password("secret123!"),
        is_active=True,
        created_at=None,
        updated_at=None,
        permissions=[],
    )


# region CREATE


@pytest.mark.anyio
async def test_create_client_success():
    """Creating a new client with a unique name should succeed and return ClientRead with secret."""

    payload = ClientCreate(name="New Client", is_active=True)

    client_repo = MagicMock()
    client_repo.read_with_filters = AsyncMock(return_value=[])
    client_repo.create = AsyncMock(return_value=make_client_obj(name=payload.name))

    permission_repo = MagicMock()

    svc = ClientService(client_repo=client_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    resp = await svc.create(payload)
    assert isinstance(resp, ClientRead) or hasattr(resp, "client_id")
    assert resp.name == "New Client"
    assert hasattr(resp, "secret") and isinstance(resp.secret, str)


@pytest.mark.anyio
async def test_create_client_duplicate_name_raises():
    """Creating a client with a name that already exists should raise EntityAlreadyExists."""

    payload = ClientCreate(name="Dup Client", is_active=True)

    client_repo = MagicMock()
    client_repo.read_with_filters = AsyncMock(return_value=[make_client_obj(name=payload.name)])

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(EntityAlreadyExists):
        await svc.create(payload)


# endregion CREATE

# region READ_BY_ID


@pytest.mark.anyio
async def test_read_by_id_not_found_raises():
    """Reading a client by ID that does not exist should raise NotFoundError."""

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=None)

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(NotFoundError):
        await svc.read_by_id(uuid4())


@pytest.mark.anyio
async def test_read_by_id_success():
    """Reading an existing client by ID should return ClientRead."""

    client = make_client_obj()

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=client)

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    result = await svc.read_by_id(client.id)
    assert isinstance(result, ClientRead)
    assert result.name == client.name


# endregion READ_BY_ID

# region UPDATE


@pytest.mark.anyio
async def test_update_client_not_found_raises():
    """Updating a non-existent client should raise NotFoundError."""

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=None)

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(NotFoundError):
        await svc.update(uuid4(), ClientUpdate(name="X"))


@pytest.mark.anyio
async def test_update_duplicate_name_raises():
    """Updating a client to a name that already exists should raise EntityAlreadyExists."""

    existing = make_client_obj(name="Old")

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=existing)
    # simulate another client with requested new name
    client_repo.read_with_filters = AsyncMock(return_value=[make_client_obj(name="New")])

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(EntityAlreadyExists):
        await svc.update(existing.id, ClientUpdate(name="New"))


@pytest.mark.anyio
async def test_update_permissions_missing_permission_raises():
    """Updating a client with a permission that does not exist should raise NotFoundError."""

    existing = make_client_obj()

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=existing)
    client_repo.update = AsyncMock(return_value=existing)

    permission_repo = MagicMock()
    permission_repo.read_by_names = AsyncMock(return_value=[])

    svc = ClientService(client_repo=client_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    payload = ClientUpdate(permissions=[{"name": "missing:perm"}])

    with pytest.raises(NotFoundError):
        await svc.update(existing.id, payload)


# endregion UPDATE

# region ASSIGN_PERMISSION


@pytest.mark.anyio
async def test_assign_permission_client_not_found_raises():
    """Assigning a permission to a non-existent client should raise NotFoundError."""

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=None)

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(NotFoundError):
        await svc.assign_permission(uuid4(), uuid4())


@pytest.mark.anyio
async def test_assign_permission_permission_not_found_raises():
    """Assigning a non-existent permission to a client should raise NotFoundError."""

    client = make_client_obj()

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=client)
    client_repo.has_permission = AsyncMock(return_value=False)

    permission_repo = MagicMock()
    permission_repo.read_by_id = AsyncMock(return_value=None)

    svc = ClientService(client_repo=client_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    with pytest.raises(NotFoundError):
        await svc.assign_permission(client.id, uuid4())


@pytest.mark.anyio
async def test_assign_permission_already_exists_raises():
    """Assigning a permission that the client already has should raise EntityAlreadyExists."""

    client = make_client_obj()

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=client)
    client_repo.has_permission = AsyncMock(return_value=True)

    permission_repo = MagicMock()
    permission_repo.read_by_id = AsyncMock(return_value=SimpleNamespace(id=uuid4(), name="perm"))

    svc = ClientService(client_repo=client_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    with pytest.raises(EntityAlreadyExists):
        await svc.assign_permission(client.id, uuid4())


# endregion ASSIGN_PERMISSION

# region REMOVE_PERMISSION


@pytest.mark.anyio
async def test_remove_permission_client_not_found_raises():
    """Removing a permission from a non-existent client should raise NotFoundError."""

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=None)

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(NotFoundError):
        await svc.remove_permission(uuid4(), uuid4())


@pytest.mark.anyio
async def test_remove_permission_not_found_raises():
    """Removing a non-existent permission from a client should raise NotFoundError."""

    client = make_client_obj()

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=client)
    client_repo.has_permission = AsyncMock(return_value=False)

    permission_repo = MagicMock()
    permission_repo.read_by_id = AsyncMock(return_value=SimpleNamespace(id=uuid4(), name="perm"))

    svc = ClientService(client_repo=client_repo, permission_repo=permission_repo, uow_factory=lambda: DummyUoW())

    with pytest.raises(NotFoundError):
        await svc.remove_permission(client.id, uuid4())


# endregion REMOVE_PERMISSION

# region DELETE


@pytest.mark.anyio
async def test_delete_client_not_found_raises():
    """Deleting a non-existent client should raise NotFoundError."""

    client_repo = MagicMock()
    client_repo.read_by_id = AsyncMock(return_value=None)

    svc = ClientService(client_repo=client_repo, permission_repo=MagicMock(), uow_factory=lambda: DummyUoW())

    with pytest.raises(NotFoundError):
        await svc.delete(uuid4())


# endregion DELETE
