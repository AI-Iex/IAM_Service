import asyncio
import logging
import sys
from pathlib import Path
from alembic.config import Config
from alembic import command
from app.db.session import get_engine
from app.core.config import settings

logger = logging.getLogger("migrate")


async def seed_permissions_and_roles(engine):
    """Seed permissions from permissions_map.json and create admin role."""

    import importlib
    import json
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Load permissions map
    perms_path = (
        Path(settings.SERVICE_PERMISSIONS_PATH)
        if isinstance(settings.SERVICE_PERMISSIONS_PATH, str)
        else settings.SERVICE_PERMISSIONS_PATH
    )

    if not perms_path.exists():
        logger.warning("permissions_map.json not found, skipping permission seeding")
        return

    # Read permissions from JSON file to a dictionary
    with perms_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        permissions_dict = data.get("permissions", {})

    # Import models dynamically
    Permission = importlib.import_module("app.models.permission").Permission
    Role = importlib.import_module("app.models.role").Role
    RolePermission = importlib.import_module("app.models.role_permission").RolePermission

    AsyncSessionFactory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with AsyncSessionFactory() as session:
        async with session.begin():

            # Insert permissions
            permission_table = Permission.__table__
            to_insert = [{"name": name, "description": desc} for name, desc in permissions_dict.items()]

            if to_insert:
                stmt = pg_insert(permission_table).values(to_insert)
                stmt = stmt.on_conflict_do_nothing(index_elements=[permission_table.c.name])
                await session.execute(stmt)

            # Create admin role
            role_table = Role.__table__
            stmt_role = pg_insert(role_table).values(
                {"name": "admin", "description": "Administrator role with all permissions"}
            )
            stmt_role = stmt_role.on_conflict_do_nothing(index_elements=[role_table.c.name])
            await session.execute(stmt_role)

            # Assign all permissions to admin role
            res_role = await session.execute(select(role_table.c.id).where(role_table.c.name == "admin").limit(1))
            role_row = res_role.first()
            if role_row:
                role_id = role_row[0]
                res_perms = await session.execute(select(permission_table.c.id))
                perm_rows = res_perms.scalars().all()

                if perm_rows:
                    rp_table = RolePermission.__table__
                    rp_inserts = [{"role_id": role_id, "permission_id": pid} for pid in perm_rows]
                    stmt_rp = pg_insert(rp_table).values(rp_inserts)
                    stmt_rp = stmt_rp.on_conflict_do_nothing(
                        index_elements=[rp_table.c.role_id, rp_table.c.permission_id]
                    )
                    await session.execute(stmt_rp)

                logger.info("Seeded %d permissions and ensured admin role", len(perm_rows))


async def main():
    """Run Alembic migrations and seed initial data."""

    engine = get_engine()

    # Run Alembic migrations
    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    logger.info("Running alembic upgrade head")
    command.upgrade(cfg, "head")
    logger.info("Alembic migrations applied successfully")

    # Seed permissions and roles
    await seed_permissions_and_roles(engine)
    logger.info("Permissions and roles seeded successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
