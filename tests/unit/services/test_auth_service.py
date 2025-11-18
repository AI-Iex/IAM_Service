import pytest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from app.services.auth import AuthService
from app.core.exceptions import DomainError, NotFoundError, UnauthorizedError
from app.schemas.user import UserRead
from app.schemas.auth import TokenPair
from app.core.security import hash_password, generate_raw_refresh_token, hash_refresh_token
from datetime import datetime, timezone, timedelta


class DummyUoW:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_user_obj(email: str = "u@example.com"):
    return SimpleNamespace(
        id=uuid4(),
        email=email,
        full_name="Test User",
        hashed_password=hash_password("TestPass1!"),
        is_superuser=False,
        roles=[],
    )


# region LOGIN


@pytest.mark.anyio
async def test_login_success():
    """Logging in with correct credentials should return UserRead and TokenPair."""

    email = "alex@example.com"
    raw_password = "TestPass1!"

    stored_user = make_user_obj(email=email)

    user_repo = MagicMock()
    user_repo.read_by_email = AsyncMock(return_value=stored_user)
    user_repo.update_last_login = AsyncMock()

    auth_user = make_user_obj(email=email)

    auth_user.roles = [SimpleNamespace(id=uuid4(), name="user", permissions=[SimpleNamespace(name="users:read")])]

    auth_repo = MagicMock()
    auth_repo.get_user_for_auth = AsyncMock(return_value=auth_user)

    refresh_repo = MagicMock()
    refresh_repo.create_refresh_token = AsyncMock()

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=user_repo,
        refresh_token_repo=refresh_repo,
        client_repo=MagicMock(),
        auth_repo=auth_repo,
    )

    result = await svc.login(email, raw_password, ip="1.2.3.4", user_agent="agent")

    assert hasattr(result, "user") and isinstance(result.user, UserRead)
    assert hasattr(result, "token") and isinstance(result.token, TokenPair)
    assert hasattr(result, "token") and hasattr(result.token, "access_token")
    assert result.token.refresh_token is not None
    assert result.token.expires_in is not None


@pytest.mark.anyio
async def test_login_user_not_found_raises():
    """Logging in with a non-existent email should raise NotFoundError."""

    user_repo = MagicMock()
    user_repo.read_by_email = AsyncMock(return_value=None)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=user_repo,
        refresh_token_repo=MagicMock(),
        client_repo=MagicMock(),
        auth_repo=MagicMock(),
    )

    with pytest.raises(UnauthorizedError):
        await svc.login("noone@example.com", "whatever")


@pytest.mark.anyio
async def test_login_wrong_password_raises():
    """Logging in with an incorrect password should raise DomainError."""

    stored_user = make_user_obj()

    user_repo = MagicMock()
    user_repo.read_by_email = AsyncMock(return_value=stored_user)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=user_repo,
        refresh_token_repo=MagicMock(),
        client_repo=MagicMock(),
        auth_repo=MagicMock(),
    )

    with pytest.raises(UnauthorizedError):
        await svc.login(stored_user.email, "badpassword")


# endregion LOGIN

# region REFRESH TOKEN


@pytest.mark.anyio
async def test_refresh_with_invalid_token_raises():
    """Refreshing with an invalid token should raise DomainError."""

    refresh_repo = MagicMock()
    refresh_repo.get_by_token_hash = AsyncMock(return_value=None)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=MagicMock(),
        refresh_token_repo=refresh_repo,
        client_repo=MagicMock(),
        auth_repo=MagicMock(),
    )

    with pytest.raises(DomainError):
        await svc.refresh_with_refresh_token("rawtoken", None)


@pytest.mark.anyio
async def test_refresh_with_valid_token_rotates():
    """Refreshing with a valid token should return new TokenPair and rotate the refresh token."""

    # Prepare a raw refresh token and jti as if it was issued earlier
    raw, jti = generate_raw_refresh_token()

    # token row as stored in DB
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    token_row = SimpleNamespace(
        jti=jti, user_id=uuid4(), revoked=False, expires_at=future, hashed_token=hash_refresh_token(raw)
    )

    refresh_repo = MagicMock()
    refresh_repo.get_refresh_token_by_jti = AsyncMock(return_value=token_row)
    refresh_repo.create_refresh_token = AsyncMock()
    refresh_repo.mark_refresh_token_replaced = AsyncMock()
    refresh_repo.update_refresh_token_last_used = AsyncMock()

    # auth repo returns user details
    user = make_user_obj()
    user.roles = [SimpleNamespace(id=uuid4(), name="user", permissions=[SimpleNamespace(name="users:read")])]
    auth_repo = MagicMock()
    auth_repo.get_user_for_auth = AsyncMock(return_value=user)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=MagicMock(),
        refresh_token_repo=refresh_repo,
        client_repo=MagicMock(),
        auth_repo=auth_repo,
    )

    result = await svc.refresh_with_refresh_token(raw, jti, ip="1.2.3.4", user_agent="agent")

    # assert new refresh token was created and replaced was marked
    assert refresh_repo.create_refresh_token.await_count == 1
    assert refresh_repo.mark_refresh_token_replaced.await_count == 1
    assert refresh_repo.update_refresh_token_last_used.await_count == 1

    assert hasattr(result, "user") and hasattr(result, "token")
    assert result.token.refresh_token is not None
    assert result.token.jti is not None
    assert str(result.token.jti) != str(jti)


# endregion REFRESH TOKEN

# region LOGOUT


@pytest.mark.anyio
async def test_logout_user_not_found_raises():
    """Logging out with a non-existent user should raise NotFoundError."""

    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=None)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=user_repo,
        refresh_token_repo=MagicMock(),
        client_repo=MagicMock(),
        auth_repo=MagicMock(),
    )

    with pytest.raises(NotFoundError):
        await svc.logout(uuid4(), uuid4())


@pytest.mark.anyio
async def test_logout_token_not_found_raises():
    """Logging out with a non-existent token should raise NotFoundError."""

    user = make_user_obj()
    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)

    refresh_repo = MagicMock()
    refresh_repo.get_refresh_token_by_jti = AsyncMock(return_value=None)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=user_repo,
        refresh_token_repo=refresh_repo,
        client_repo=MagicMock(),
        auth_repo=MagicMock(),
    )

    with pytest.raises(NotFoundError):
        await svc.logout(user.id, uuid4())


@pytest.mark.anyio
async def test_logout_token_belongs_to_other_user_raises():
    """Logging out with a token that belongs to a different user should raise DomainError."""

    user = make_user_obj()
    user_repo = MagicMock()
    user_repo.read_by_id = AsyncMock(return_value=user)

    # token refers to a different user
    token_row = SimpleNamespace(user_id=uuid4(), revoked=False)

    refresh_repo = MagicMock()
    refresh_repo.get_refresh_token_by_jti = AsyncMock(return_value=token_row)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=user_repo,
        refresh_token_repo=refresh_repo,
        client_repo=MagicMock(),
        auth_repo=MagicMock(),
    )

    with pytest.raises(DomainError):
        await svc.logout(user.id, uuid4())


# endregion LOGOUT

# region CLIENT CREDENTIALS


@pytest.mark.anyio
async def test_client_credentials_success_and_failure():
    """Testing client credentials flow for both success and failure cases."""

    # success

    client = SimpleNamespace(
        id=uuid4(), client_id=uuid4(), is_active=True, hashed_secret=hash_password("secret123"), permissions=[]
    )

    client_repo = MagicMock()
    client_repo.read_by_clientid = AsyncMock(return_value=client)

    svc = AuthService(
        uow_factory=lambda: DummyUoW(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        client_repo=client_repo,
        auth_repo=MagicMock(),
    )

    token = await svc.client_credentials(client.client_id, "secret123")
    assert hasattr(token, "access_token") and token.refresh_token is None

    # failure: wrong secret

    client_repo.read_by_clientid = AsyncMock(return_value=client)
    with pytest.raises(UnauthorizedError):
        await svc.client_credentials(client.client_id, "wrong")


# endregion CLIENT CREDENTIALS
