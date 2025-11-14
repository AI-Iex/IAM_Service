import pytest
from sqlalchemy import select
from app.db.bootstrap import seed_permissions_and_roles, create_default_superuser
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.core.config import settings

@pytest.mark.anyio
async def test_seed_permissions_and_roles(engine, db_session):

    """Run the seeding function and verify permissions and admin role are created."""

    # Ensure starting state: no admin role
    r = await db_session.execute(select(Role).where(Role.name == "admin"))
    assert r.first() is None

    await seed_permissions_and_roles(engine)

    # Verify admin role exists
    r2 = await db_session.execute(select(Role).where(Role.name == "admin"))
    role_row = r2.scalars().first()
    assert role_row is not None

    # Verify at least one permission from permissions_map exists
    p = await db_session.execute(select(Permission).limit(1))
    assert p.scalars().first() is not None

@pytest.mark.anyio
async def test_create_default_superuser(engine, db_session, monkeypatch):

    """Create a default superuser via the bootstrap helper when the settings enable it."""
    
    # Enable creation and set test credentials
    monkeypatch.setattr(settings, "CREATE_SUPERUSER_ON_STARTUP", True)
    test_email = "bootstrap_admin@example.com"
    monkeypatch.setattr(settings, "SUPERUSER_EMAIL", test_email)
    monkeypatch.setattr(settings, "SUPERUSER_PASSWORD", "ChangeMe123!")
    monkeypatch.setattr(settings, "SUPERUSER_NAME", "Bootstrap Admin")

    # Before creation, ensure no such user exists
    res = await db_session.execute(select(User).where(User.email == test_email))
    assert res.scalars().first() is None

    await create_default_superuser(engine)

    # User should now exist and be superuser
    res2 = await db_session.execute(select(User).where(User.email == test_email))
    user = res2.scalars().first()
    assert user is not None and user.is_superuser is True
