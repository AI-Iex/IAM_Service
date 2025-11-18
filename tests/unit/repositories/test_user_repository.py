import pytest
from app.core.exceptions import EntityAlreadyExists
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.schemas.user import UserCreateInDB, UserUpdateInDB
from app.schemas.role import RoleCreate
from app.core.security import hash_password
import uuid


def _make_user_dto(email: str, full_name: str, is_active: bool, is_superuser: bool) -> UserCreateInDB:
    """Creates a UserCreateInDB DTO for testing."""

    return UserCreateInDB(
        email=email,
        full_name=full_name,
        hashed_password=hash_password("testpasS_123"),
        is_active=is_active,
        is_superuser=is_superuser,
        require_password_change=False,
    )


# region CREATE


@pytest.mark.anyio
async def test_create_user(db_session):
    """Test creating a user via UserRepository."""

    user_repo = UserRepository()

    dto = _make_user_dto("create@example.com", "Create User", True, False)

    user = await user_repo.create(db_session, dto)
    assert user.email == "create@example.com"


@pytest.mark.anyio
async def test_duplicate_create_raises(db_session):
    """Test that creating a user with duplicate email raises EntityAlreadyExists."""

    user_repo = UserRepository()

    dto = _make_user_dto("dupli@example.com", "Duplicate User", True, False)

    await user_repo.create(db_session, dto)

    with pytest.raises(EntityAlreadyExists):
        await user_repo.create(db_session, dto)


# endregion CREATE

# region READ


@pytest.mark.anyio
async def test_read_by_email(db_session):
    """Test reading a user by email."""

    user_repo = UserRepository()

    dto = _make_user_dto("read@example.com", "Read User", False, False)

    created = await user_repo.create(db_session, dto)

    found = await user_repo.read_by_email(db_session, "read@example.com")

    assert found is not None and found.id == created.id


@pytest.mark.anyio
async def test_read_with_filters(db_session):
    """Test reading users with filters on name and email."""

    user_repo = UserRepository()

    await user_repo.create(db_session, _make_user_dto("f1@example.com", "Filter One", True, False))
    await user_repo.create(db_session, _make_user_dto("f2@example.com", "Filter Two", False, True))

    res = await user_repo.read_with_filters(db_session, name="Filter")
    emails = [u.email for u in res]

    assert "f1@example.com" in emails and "f2@example.com" in emails

    res2 = await user_repo.read_with_filters(db_session, email=["f1@example.com", "f2@example.com"])

    assert len(res2) == 2

    active = await user_repo.read_with_filters(db_session, active=True)
    assert any(u.email == "f1@example.com" for u in active)

    supers = await user_repo.read_with_filters(db_session, is_superuser=True)
    assert any(u.email == "f2@example.com" for u in supers)

    empty_res = await user_repo.read_with_filters(db_session, name="Nonexistent")
    assert len(empty_res) == 0


@pytest.mark.anyio
async def test_read_by_id_not_found(db_session):
    """Test reading a user by ID that does not exist returns None."""

    user_repo = UserRepository()
    notfound = await user_repo.read_by_id(db_session, uuid.uuid4())
    assert notfound is None


# endregion READ

# region UPDATE


@pytest.mark.anyio
async def test_update_last_login(db_session):
    """Test updating the last login timestamp of a user."""

    user_repo = UserRepository()

    dto = _make_user_dto("login@example.com", "Login User", True, False)

    user = await user_repo.create(db_session, dto)

    updated = await user_repo.update_last_login(db_session, user.id)
    assert updated.last_login is not None


@pytest.mark.anyio
async def test_assign_and_has_role(db_session):
    """Test assigning a role to a user and checking if the user has that role."""

    user_repo = UserRepository()
    role_repo = RoleRepository()

    role = await role_repo.create(db_session, RoleCreate(name="rtest", description="r"))
    user = await user_repo.create(db_session, _make_user_dto("assign@example.com", "Assign User", False, False))

    await user_repo.assign_role(db_session, user.id, role.id)
    assert await user_repo.has_role(db_session, user.id, role.id) is True


@pytest.mark.anyio
async def test_remove_role(db_session):
    """Test removing a role from a user."""

    user_repo = UserRepository()
    role_repo = RoleRepository()
    role = await role_repo.create(db_session, RoleCreate(name="rrem", description="r"))
    user = await user_repo.create(db_session, _make_user_dto("rem@example.com", "Rem User", False, False))

    await user_repo.assign_role(db_session, user.id, role.id)
    await user_repo.remove_role(db_session, user.id, role.id)
    assert await user_repo.has_role(db_session, user.id, role.id) is False


@pytest.mark.anyio
async def test_update_user(db_session):
    """Test updating user details."""

    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("up@example.com", "Up User", False, False))

    upd = UserUpdateInDB(full_name="Updated")

    user2 = await user_repo.update(db_session, user.id, upd)
    assert user2.full_name == "Updated"

    upd2 = UserUpdateInDB(is_active=True)
    user3 = await user_repo.update(db_session, user.id, upd2)
    assert user3.is_active is True

    upd3 = UserUpdateInDB(is_superuser=True)
    user4 = await user_repo.update(db_session, user.id, upd3)
    assert user4.is_superuser is True


# endregion UPDATE

# region DELETE


@pytest.mark.anyio
async def test_delete_user(db_session):
    """Test deleting a user."""

    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("del@example.com", "Del User", False, False))
    await user_repo.delete(db_session, user.id)
    found = await user_repo.read_by_email(db_session, "del@example.com")
    assert found is None


# endregion DELETE
