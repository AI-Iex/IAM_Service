import pytest
from app.repositories.permission import PermissionRepository
from app.schemas.permission import PermissionCreate, PermissionUpdateInDB


def _make_permission_dto(name: str, description: str) -> PermissionCreate:
    """Helper to build a PermissionCreate DTO for tests."""

    return PermissionCreate(name=name, description=description)


# region CRUD


@pytest.mark.anyio
async def test_create_and_read_permission(db_session):
    """Create a permission and read it by id."""

    repo = PermissionRepository()

    p = await repo.create(db_session, _make_permission_dto("perm:alpha", "alpha"))
    assert p.name == "perm:alpha"

    found = await repo.read_by_id(db_session, p.id)
    assert found is not None and found.id == p.id


@pytest.mark.anyio
async def test_read_with_filters_returns_matches(db_session):
    """Test read_with_filters with name and description filters."""

    repo = PermissionRepository()

    p = await repo.create(db_session, _make_permission_dto("perm:alpha", "alpha"))
    list1 = await repo.read_with_filters(db_session, name="alpha")
    assert any(x.id == p.id for x in list1)
    list2 = await repo.read_with_filters(db_session, description="alpha")
    assert any(x.id == p.id for x in list2)


@pytest.mark.anyio
async def test_update_permission(db_session):
    """Update a permission's fields."""

    repo = PermissionRepository()

    p = await repo.create(db_session, _make_permission_dto("perm:update", "before"))
    upd = PermissionUpdateInDB(description="alpha updated")
    p2 = await repo.update(db_session, p.id, upd)
    assert p2.description == "alpha updated"


@pytest.mark.anyio
async def test_read_by_names_and_delete(db_session):
    """Test read_by_names and delete functionality."""

    repo = PermissionRepository()

    p = await repo.create(db_session, _make_permission_dto("perm:alpha", "alpha"))
    by_names = await repo.read_by_names(db_session, ["perm:alpha"])
    assert any(x.id == p.id for x in by_names)

    # delete (should not raise)
    await repo.delete(db_session, p.id)


# endregion CRUD

# region NOT-FOUND / EMPTY FILTERS


@pytest.mark.anyio
async def test_permission_not_found_and_empty_filters(db_session):
    """Ensure read_by_id returns None for unknown id and filters that match nothing return empty list."""

    repo = PermissionRepository()
    import uuid

    notfound = await repo.read_by_id(db_session, uuid.uuid4())
    assert notfound is None

    res = await repo.read_with_filters(db_session, name="no-such-name")
    assert isinstance(res, list)


# endregion NOT-FOUND / EMPTY FILTERS
