import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from uuid import uuid4

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
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
        # create an async session factory bound to the provided engine
        AsyncSessionFactory = async_sessionmaker(bind=engine, expire_on_commit=False)

        async with AsyncSessionFactory() as session:
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
        # Use async_sessionmaker and perform core-level upserts to avoid
        # ORM relationship lazy-loads that may trigger unexpected sync IO.
        AsyncSessionFactory = async_sessionmaker(bind=engine, expire_on_commit=False)

        async with AsyncSessionFactory() as session:
            async with session.begin():
                # Insert permissions using ON CONFLICT DO NOTHING so this is idempotent
                permission_table = Permission.__table__
                to_insert = []
                for name, desc in permissions_dict.items():
                    to_insert.append({"name": name, "description": desc})

                if to_insert:
                    stmt = pg_insert(permission_table).values(to_insert)
                    stmt = stmt.on_conflict_do_nothing(index_elements=[permission_table.c.name])
                    await session.execute(stmt)

                # Ensure admin role exists (insert if missing)
                role_table = Role.__table__
                stmt_role = pg_insert(role_table).values({"name": "admin", "description": "Administrator role with all permissions"})
                stmt_role = stmt_role.on_conflict_do_nothing(index_elements=[role_table.c.name])
                await session.execute(stmt_role)

                # Fetch role id and all permission ids
                res_role = await session.execute(select(role_table.c.id).where(role_table.c.name == "admin").limit(1))
                role_row = res_role.first()
                if not role_row:
                    # unexpected, but abort gracefully
                    logger.error("Failed to obtain admin role id after upsert")
                    return
                role_id = role_row[0]

                res_perms = await session.execute(select(permission_table.c.id))
                perm_rows = res_perms.scalars().all()

                # Upsert role_permissions entries (idempotent)
                if perm_rows:
                    rp_table = RolePermission.__table__
                    rp_inserts = []
                    for pid in perm_rows:
                        rp_inserts.append({"role_id": role_id, "permission_id": pid})

                    stmt_rp = pg_insert(rp_table).values(rp_inserts)
                    stmt_rp = stmt_rp.on_conflict_do_nothing(index_elements=[rp_table.c.role_id, rp_table.c.permission_id])
                    await session.execute(stmt_rp)

                logger.info("Seeded %d permissions and ensured admin role", len(perm_rows))

    except SQLAlchemyError as exc:
        logger.exception("Database error while seeding permissions: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Unexpected error while seeding permissions: %s", exc)
        raise


async def _ensure_admin_role(session: AsyncSession) -> Optional[Role]:

    """Helper (legacy): ensure an 'admin' role exists in the provided session and return it.

    NOTE: This helper is kept for compatibility but is no longer used by the primary
    seeding function which uses core upserts to avoid lazy-loads during startup.
    """

    try:
        res = await session.execute(select(Role).filter_by(name="admin").limit(1))
        admin_role = res.scalars().first()
        return admin_role
    except Exception:
        logger.exception("Error ensuring admin role")
        return None
