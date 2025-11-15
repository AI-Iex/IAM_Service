import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateInDB
from app.core.security import hash_password


def _make_user_dto(email: str, full_name: str, is_active: bool = True, is_superuser: bool = False) -> UserCreateInDB:
    
    '''Creates a UserCreateInDB DTO for testing.'''

    return UserCreateInDB(
        email = email,
        full_name = full_name,
        hashed_password = hash_password("testpasS_123"),
        is_active = is_active,
        is_superuser = is_superuser,
        require_password_change = False,
    )

# region CREATE / READ

@pytest.mark.anyio
async def test_create_and_get_by_hash(db_session):

    """Create a refresh token and retrieve it by its hashed value."""

    repo = RefreshTokenRepository()
    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("rt_user1@example.com", "RT User 1"))
    jti = uuid4()
    user_id = user.id
    expires = datetime.now(timezone.utc) + timedelta(days=1)

    rt = await repo.create_refresh_token(db_session, jti, user_id, "h1", expires, user_agent="ua", client_ip="1.2.3.4")
    assert rt.jti == jti

    by_hash = await repo.get_by_token_hash(db_session, "h1")
    assert by_hash is not None and by_hash.jti == jti

@pytest.mark.anyio
async def test_get_refresh_token_by_jti(db_session):

    """Retrieve a refresh token using its JTI."""

    repo = RefreshTokenRepository()
    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("rt_user2@example.com", "RT User 2"))
    jti = uuid4()
    user_id = user.id
    expires = datetime.now(timezone.utc) + timedelta(days=1)

    await repo.create_refresh_token(db_session, jti, user_id, "h2", expires)
    row = await repo.get_refresh_token_by_jti(db_session, jti)
    assert row is not None and row.jti == jti

# endregion CREATE / READ

# region UPDATE / FLAGS

@pytest.mark.anyio
async def test_update_last_used(db_session):

    """Update the last_used_at timestamp for a refresh token."""

    repo = RefreshTokenRepository()
    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("rt_user3@example.com", "RT User 3"))
    jti = uuid4()
    user_id = user.id
    expires = datetime.now(timezone.utc) + timedelta(days=1)

    await repo.create_refresh_token(db_session, jti, user_id, "h3", expires)
    await repo.update_refresh_token_last_used(db_session, jti)
    updated = await repo.get_refresh_token_by_jti(db_session, jti)
    assert updated.last_used_at is not None

@pytest.mark.anyio
async def test_revoke_refresh_token(db_session):

    """Mark a refresh token revoked and verify its revoked flag."""

    repo = RefreshTokenRepository()
    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("rt_user4@example.com", "RT User 4"))
    jti = uuid4()
    user_id = user.id
    expires = datetime.now(timezone.utc) + timedelta(days=1)

    await repo.create_refresh_token(db_session, jti, user_id, "h4", expires)
    await repo.revoke_refresh_token(db_session, jti)
    rt = await repo.get_refresh_token_by_jti(db_session, jti)
    assert rt.revoked is True

@pytest.mark.anyio
async def test_mark_refresh_token_replaced(db_session):

    """Mark a token as replaced by another JTI and verify the replaced_by value."""

    repo = RefreshTokenRepository()
    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("rt_user5@example.com", "RT User 5"))
    jti = uuid4()
    new_jti = uuid4()
    user_id = user.id
    expires = datetime.now(timezone.utc) + timedelta(days=1)

    await repo.create_refresh_token(db_session, jti, user_id, "h5", expires)
    await repo.mark_refresh_token_replaced(db_session, jti, new_jti)
    rt = await repo.get_refresh_token_by_jti(db_session, jti)
    assert rt.replaced_by == new_jti

@pytest.mark.anyio
async def test_revoke_all_refresh_tokens_for_user(db_session):

    """Revoke all tokens for a user and verify all are flagged revoked."""

    repo = RefreshTokenRepository()
    user_repo = UserRepository()

    user = await user_repo.create(db_session, _make_user_dto("rt_user6@example.com", "RT User 6"))
    user_id = user.id
    expires = datetime.now(timezone.utc) + timedelta(days=1)

    j1 = uuid4()
    j2 = uuid4()
    await repo.create_refresh_token(db_session, j1, user_id, "ha1", expires)
    await repo.create_refresh_token(db_session, j2, user_id, "ha2", expires)

    await repo.revoke_all_refresh_tokens_for_user(db_session, user_id)

    r1 = await repo.get_by_token_hash(db_session, "ha1")
    r2 = await repo.get_by_token_hash(db_session, "ha2")
    assert r1.revoked is True and r2.revoked is True

# endregion UPDATE / FLAGS

