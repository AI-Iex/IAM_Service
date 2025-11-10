import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import uuid4

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.permission import Permission
from app.models.role import Role
import json
from pathlib import Path

logger = logging.getLogger(__name__)


async def create_default_superuser(engine) -> None:

    """Create or promote a default superuser using the provided AsyncEngine.

    Behaviour:
    - If CREATE_SUPERUSER_ON_STARTUP is False, the caller should avoid calling this function.
    - If SUPERUSER_EMAIL or SUPERUSER_PASSWORD are missing, the function logs and returns.
    - If an existing superuser exists, nothing is done.
    - If a user exists with SUPERUSER_EMAIL, skip creation.
    - Otherwise a new user is created with the provided credentials and marked as superuser.

    Uses an AsyncSession bound to the engine and performs safe commit/rollback.
    """

    if not getattr(settings, "CREATE_SUPERUSER_ON_STARTUP", False):
        logger.debug("CREATE_SUPERUSER_ON_STARTUP is False - skipping superuser creation")
        return

    email: Optional[str] = getattr(settings, "SUPERUSER_EMAIL", None)
    password: Optional[str] = getattr(settings, "SUPERUSER_PASSWORD", None)
    full_name: str = getattr(settings, "SUPERUSER_NAME", "Default Superuser")

    if not email or not password:
        logger.warning("Superuser credentials not configured (SUPERUSER_EMAIL/SUPERUSER_PASSWORD); skipping creation")
        return

    try:
        async with AsyncSession(engine) as session:

            async with session.begin():
                # 1. If any superuser exists, skip creation.
                res = await session.execute(select(User).filter_by(is_superuser=True).limit(1))
                existing_super = res.scalars().first()
                if existing_super:
                    logger.info("Superuser already exists; skipping creation.")
                    return

                # 2) If user with the configured email exists, skip creation.
                res2 = await session.execute(select(User).filter_by(email=email).limit(1))
                existing_by_email = res2.scalars().first()
                if existing_by_email:
                    logger.warning("User with the configured email exists; skipping creation (email=%s)", email)
                    return

                # 3) Create new superuser
                hashed = hash_password(password)
                new_user = User(
                    id = uuid4(),
                    full_name = full_name,
                    email = email,
                    hashed_password = hashed,
                    is_superuser = True,
                    is_active = True,
                    require_password_change = True,
                )
                session.add(new_user)
                await session.flush()
                
                logger.info("Created default superuser (id=%s).", new_user.id)


    except SQLAlchemyError as exc:
        logger.exception("Database error while creating default superuser: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Unexpected error while creating default superuser: %s", exc)
        raise


async def seed_permissions_and_roles(engine) -> None:

    """Create permissions and a default 'admin' role based on `permissions_map.json`.

    - Reads `app/config/permissions_map.json` and creates Permission records if missing.
    - Ensures an 'admin' Role exists and is granted all permissions.
    """

    perms_path = Path(__file__).parent.parent / "config" / "permissions_map.json"
    if not perms_path.exists():
        logger.warning("permissions_map.json not found at %s, skipping permission seeding", perms_path)
        return

    try:
        with perms_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            permissions_dict = data.get("permissions", {})
    except Exception as exc:
        logger.exception("Failed to read permissions_map.json: %s", exc)
        return

    try:
        async with AsyncSession(engine) as session:
            # create missing permissions
            for name, desc in permissions_dict.items():
                res = await session.execute(select(Permission).filter_by(name=name).limit(1))
                existing = res.scalars().first()
                if not existing:
                    p = Permission(name=name, description=desc)
                    session.add(p)
            await session.commit()

            # ensure admin role exists and has all permissions
            res = await session.execute(select(Role).filter_by(name="admin").limit(1))
            admin_role = res.scalars().first()
            if not admin_role:
                admin_role = Role(name="admin", description="Administrator role with all permissions")
                session.add(admin_role)
                await session.flush()

            # refresh permissions from DB and attach to admin role
            res_all = await session.execute(select(Permission))
            all_perms = res_all.scalars().all()
            admin_role.permissions = all_perms
            session.add(admin_role)
            await session.commit()
            logger.info("Seeded %d permissions and ensured admin role", len(all_perms))

    except SQLAlchemyError as exc:
        logger.exception("Database error while seeding permissions: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Unexpected error while seeding permissions: %s", exc)
        raise


async def _ensure_admin_role(session: AsyncSession) -> Role | None:

    """Helper: ensure an 'admin' role exists in the provided session and return it."""

    try:
        res = await session.execute(select(Role).filter_by(name="admin").limit(1))
        admin_role = res.scalars().first()
        if not admin_role:
            admin_role = Role(name="admin", description="Administrator role with all permissions")
            session.add(admin_role)
            await session.flush()

        # attach all permissions
        res_all = await session.execute(select(Permission))
        all_perms = res_all.scalars().all()
        admin_role.permissions = all_perms
        session.add(admin_role)
        await session.commit()
        return admin_role
    except Exception:
        logger.exception("Error ensuring admin role")
        return None
