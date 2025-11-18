import pytest
from sqlalchemy import select
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


@pytest.mark.anyio
async def test_seed_permissions_and_roles(engine, db_session):
    """Test that migrate_and_seed.py creates permissions and admin role."""
    from scripts.migrate_and_seed import seed_permissions_and_roles

    # Ensure starting state: no admin role
    r = await db_session.execute(select(Role).where(Role.name == "admin"))
    assert r.first() is None

    # Run the actual seeding function
    await seed_permissions_and_roles(engine)

    # Verify admin role exists
    await db_session.commit()  # Refresh session to see new data
    r2 = await db_session.execute(select(Role).where(Role.name == "admin"))
    role_row = r2.scalars().first()
    assert role_row is not None, "Admin role should be created"

    # Verify at least one permission from permissions_map exists
    p = await db_session.execute(select(Permission).limit(1))
    assert p.scalars().first() is not None, "Permissions should be seeded"


@pytest.mark.anyio
async def test_create_default_superuser(engine, db_session, monkeypatch):
    """Test that create_superuser.py creates a superuser when configured."""
    from scripts.create_superuser import create_default_superuser
    from app.core.config import settings

    # Enable creation and set test credentials
    monkeypatch.setattr(settings, "CREATE_SUPERUSER_ON_STARTUP", True)
    test_email = "bootstrap_admin@example.com"
    monkeypatch.setattr(settings, "SUPERUSER_EMAIL", test_email)
    monkeypatch.setattr(settings, "SUPERUSER_PASSWORD", "ChangeMe123!")
    monkeypatch.setattr(settings, "SUPERUSER_NAME", "Bootstrap Admin")

    # Before creation, ensure no such user exists
    res = await db_session.execute(select(User).where(User.email == test_email))
    assert res.scalars().first() is None

    # Run the actual superuser creation function
    result = await create_default_superuser(engine)
    assert result == 0, "Superuser creation should succeed"

    # User should now exist and be superuser
    await db_session.commit()  # Refresh session to see new data
    res2 = await db_session.execute(select(User).where(User.email == test_email))
    user = res2.scalars().first()
    assert user is not None, "Superuser should be created"
    assert user.is_superuser is True, "User should be a superuser"
    assert user.is_active is True, "Superuser should be active"
