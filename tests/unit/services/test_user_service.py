import pytest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from app.services.user import UserService
from app.core.exceptions import EntityAlreadyExists, DomainError, NotFoundError
from app.schemas.user import UserRegister, UserCreateByAdmin, UserRead, UserUpdate, UserChangeEmail, PasswordChange
from app.core.security import hash_password

# A permissive policy for unit tests to avoid relying on external business config files
PERMISSIVE_POLICY = {
    "email_policy": {"min_length": 1, "max_length": 255, "valid_domains": []},
    "password_policy": {
        "min_length": 6,
        "character_requirements": {
            "uppercase": {"required": False, "min_count": 0},
            "numbers": {"required": False, "min_count": 0},
            "special_chars": {"required": False, "allowed_chars": "!@#$%^&*()", "min_count": 0},
        },
    },
    "name_policy": {"min_length": 1},
}


class DummyUoW:
    """A minimal async context manager to stand in for UnitOfWork in tests."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_user_obj(email: str = "u@example.com"):
    """Return a simple namespace that mimics the attributes expected by schemas."""

    return SimpleNamespace(
        id=uuid4(),
        email=email,
        full_name="Test User",
        hashed_password=hash_password("TestPass1!"),
        is_active=True,
        is_superuser=False,
        require_password_change=False,
        created_at=None,
        updated_at=None,
        last_login=None,
        roles=[],
    )


# region REGISTER


@pytest.mark.anyio
async def test_register_user_success():
    """Registering a new user with unique email should succeed and return UserRead."""

    payload = UserRegister(email="new@example.com", full_name="New User", password="StrongPass1!")

    user_repo = MagicMock()
    user_repo.read_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(return_value=make_user_obj(email=payload.email))

    role_repo = MagicMock()

    svc = UserService(user_repo=user_repo, role_repo=role_repo, uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    user = await svc.register_user(payload)
    assert isinstance(user, UserRead)
    assert user.email == "new@example.com"


@pytest.mark.anyio
async def test_register_user_existing_email_raises():
    """Registering a user with an existing email should raise EntityAlreadyExists."""

    payload = UserRegister(email="dup@example.com", full_name="Dup User", password="StrongPass1!")

    user_repo = MagicMock()
    user_repo.read_by_email = AsyncMock(return_value=make_user_obj(email=payload.email))

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    with pytest.raises(EntityAlreadyExists):
        await svc.register_user(payload)


# endregion REGISTER

# region CREATE


@pytest.mark.anyio
async def test_create_by_admin_sets_require_password_change():
    """Creating a user via admin service method must set require_password_change to True."""

    payload = UserCreateByAdmin(
        email="admincreate@example.com",
        full_name="Admin Create",
        password="StrongPass1!",
        is_active=True,
        is_superuser=False,
    )

    # Ensure the repo receives require_password_change True from service (the input given to create)
    async def create_side_effect(db, dto):
        assert getattr(dto, "require_password_change", None) is True
        return make_user_obj(email=dto.email)

    user_repo = MagicMock()
    user_repo.read_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(side_effect=create_side_effect)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY
    user = await svc.create(payload)
    assert user.email == "admincreate@example.com"


@pytest.mark.anyio
async def test_create_user_existing_email_raises():
    """Creating a user with an existing email should raise EntityAlreadyExists."""

    payload = UserCreateByAdmin(
        email="dup2@example.com", full_name="Dup User 2", password="StrongPass1!", is_active=True, is_superuser=False
    )

    user_repo = MagicMock()
    user_repo.read_by_email = AsyncMock(return_value=make_user_obj(email=payload.email))

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    with pytest.raises(EntityAlreadyExists):
        await svc.create(payload)


# endregion CREATE

# region READ_BY_ID


@pytest.mark.anyio
async def test_read_by_id_success():
    """Reading an existing user by ID should return UserRead."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    result = await svc.read_by_id(user.id)
    assert isinstance(result, UserRead)
    assert result.email == user.email


@pytest.mark.anyio
async def test_read_by_id_not_found_raises():
    """Reading a user by ID that does not exist should raise NotFoundError."""

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=None)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY
    with pytest.raises(NotFoundError):
        await svc.read_by_id(uuid4())


# endregion READ_BY_ID

# region UPDATE


@pytest.mark.anyio
async def test_update_user_missing_role_raises():
    """Updating a user to assign a role that does not exist should raise NotFoundError."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)
    user_repo.update = AsyncMock(return_value=user)

    role_repo = MagicMock()
    role_repo.read_by_names = AsyncMock(return_value=[])

    svc = UserService(user_repo=user_repo, role_repo=role_repo, uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    payload = UserUpdate(roles=["admin"])
    with pytest.raises(NotFoundError):
        await svc.update(user.id, payload)


@pytest.mark.anyio
async def test_update_user_not_found_raises():
    """Updating a non found user to assign a role should raise NotFoundError."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=None)
    user_repo.update = AsyncMock(return_value=user)

    role_repo = MagicMock()
    role_repo.read_by_names = AsyncMock(return_value=[])

    svc = UserService(user_repo=user_repo, role_repo=role_repo, uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    payload = UserUpdate(roles=["admin"])
    with pytest.raises(NotFoundError):
        await svc.update(user.id, payload)


# endregion UPDATE

# region CHANGE_EMAIL


@pytest.mark.anyio
async def test_change_email_current_mismatch_raises():
    """Changing email with incorrect current email should raise DomainError."""

    user = make_user_obj(email="old@example.com")

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    payload = UserChangeEmail(
        current_email="wrong@example.com", new_email="new@example.com", current_password="password"
    )
    with pytest.raises(DomainError):
        await svc.change_email(user.id, payload)


@pytest.mark.anyio
async def test_change_email_new_exists_raises():
    """Changing email with existing new email should raise EntityAlreadyExists."""

    user = make_user_obj(email="old@example.com")

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)
    user_repo.read_by_email = AsyncMock(return_value=make_user_obj(email="new@example.com"))

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    payload = UserChangeEmail(
        current_email="old@example.com", new_email="new@example.com", current_password="TestPass1!"
    )
    with pytest.raises(EntityAlreadyExists):
        await svc.change_email(user.id, payload)


@pytest.mark.anyio
async def test_change_email_password_mismatch_raises():
    """Changing email with incorrect current password should raise DomainError."""

    user = make_user_obj(email="old@example.com")

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)
    user_repo.read_by_email = AsyncMock(return_value=make_user_obj(email="new@example.com"))

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    payload = UserChangeEmail(
        current_email="old@example.com", new_email="new@example.com", current_password="WrongPass"
    )
    with pytest.raises(DomainError):
        await svc.change_email(user.id, payload)


# endregion CHANGE_EMAIL

# region CHANGE_PASSWORD


@pytest.mark.anyio
async def test_change_password_wrong_old_raises():
    """Changing password with incorrect old password should raise DomainError."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    payload = PasswordChange(old_password="bad", new_password="NewStrong1!")
    with pytest.raises(DomainError):
        await svc.change_password(user.id, payload)


@pytest.mark.anyio
async def test_change_password_not_different_raises():
    """Changing password with the same password as the old password should raise DomainError."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY

    payload = PasswordChange(old_password="NewStrong1!", new_password="NewStrong1!")
    with pytest.raises(DomainError):
        await svc.change_password(user.id, payload)


# endregion CHANGE_PASSWORD

# region ASSIGN_ROLE


@pytest.mark.anyio
async def test_assign_role_user_not_found_raises():
    """Assigning a role to a non-existent user should raise NotFoundError."""

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=None)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.assign_role(uuid4(), uuid4())


@pytest.mark.anyio
async def test_assign_role_role_not_found_raises():
    """Assigning a non-existent role to a user should raise NotFoundError."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)
    user_repo.has_role = AsyncMock(return_value=False)

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=None)

    svc = UserService(user_repo=user_repo, role_repo=role_repo, uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY
    with pytest.raises(NotFoundError):
        await svc.assign_role(user.id, uuid4())


@pytest.mark.anyio
async def test_assign_role_already_has_role_raises():
    """Assigning a role to a user who already has it should raise EntityAlreadyExists."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)
    user_repo.has_role = AsyncMock(return_value=True)

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=SimpleNamespace(id=uuid4(), name="admin"))
    svc = UserService(user_repo=user_repo, role_repo=role_repo, uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY
    with pytest.raises(EntityAlreadyExists):
        await svc.assign_role(user.id, uuid4())


# endregion ASSIGN_ROLE

# region REMOVE_ROLE


@pytest.mark.anyio
async def test_remove_role_user_not_found_raises():
    """Removing a role from a non-existent user should raise NotFoundError."""

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=None)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    with pytest.raises(NotFoundError):
        await svc.remove_role(uuid4(), uuid4())


@pytest.mark.anyio
async def test_remove_role_role_not_found_raises():
    """Removing a non-existent role from a user should raise NotFoundError."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)
    user_repo.has_role = AsyncMock(return_value=False)

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=None)

    svc = UserService(user_repo=user_repo, role_repo=role_repo, uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY
    with pytest.raises(NotFoundError):
        await svc.remove_role(user.id, uuid4())


@pytest.mark.anyio
async def test_remove_role_without_having_role_raises():
    """Removing a role from a user who does not have it should raise NotFoundError."""

    user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)
    user_repo.has_role = AsyncMock(return_value=False)

    role_repo = MagicMock()
    role_repo.read_by_id = AsyncMock(return_value=SimpleNamespace(id=uuid4(), name="admin"))
    svc = UserService(user_repo=user_repo, role_repo=role_repo, uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY
    with pytest.raises(NotFoundError):
        await svc.remove_role(user.id, uuid4())


# endregion REMOVE_ROLE

# region DELETE


@pytest.mark.anyio
async def test_delete_user_not_found_raises():
    """Deleting a non-existent user should raise NotFoundError."""

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=None)

    svc = UserService(user_repo=user_repo, role_repo=MagicMock(), uow_factory=lambda: DummyUoW())
    svc._policy = PERMISSIVE_POLICY
    with pytest.raises(NotFoundError):
        await svc.delete(uuid4())


# endregion DELETE
