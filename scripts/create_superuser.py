import asyncio
import logging
import sys
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_engine

logger = logging.getLogger("create_superuser")

async def create_default_superuser(engine) -> int:

    """Create a default superuser if configured and none exists."""

    # Check if creation is enabled
    if not getattr(settings, "CREATE_SUPERUSER_ON_STARTUP", False):
        logger.info("CREATE_SUPERUSER_ON_STARTUP is not set; aborting superuser creation")
        return 0

    # Get superuser credentials from settings
    email = getattr(settings, "SUPERUSER_EMAIL", None)
    password = getattr(settings, "SUPERUSER_PASSWORD", None)
    full_name = getattr(settings, "SUPERUSER_NAME", "Default Superuser")

    if not email or not password:
        logger.error("SUPERUSER_EMAIL and SUPERUSER_PASSWORD must be set to create a superuser")
        return 2

    try:
        async with engine.begin() as conn:

            # 1. If any superuser exists, do nothing
            res = await conn.execute(text("SELECT id FROM users WHERE is_superuser = true LIMIT 1"))
            row = res.first()
            if row:
                logger.info("A superuser already exists; nothing to do")
                return 0

            # 2. If a user with the configured email exists, warn and skip
            res2 = await conn.execute(text("SELECT id FROM users WHERE email = :email LIMIT 1"), {"email": email})
            row2 = res2.first()
            if row2:
                logger.warning("User with email %s already exists; skipping superuser creation", email)
                return 0

            # 3. Insert the new superuser using SQL core
            new_id = str(uuid4())
            hashed = hash_password(password)

            await conn.execute(
                text(
                    "INSERT INTO users (id, full_name, email, hashed_password, is_superuser, is_active, require_password_change) "
                    "VALUES (:id, :full_name, :email, :hashed_password, true, true, true)"
                ),
                {"id": new_id, "full_name": full_name, "email": email, "hashed_password": hashed},
            )

            logger.info("Created default superuser (email=%s id=%s)", email, new_id)
            return 0

    except Exception as exc:
        logger.exception("Error while creating superuser: %s", exc)
        return 3

async def main() -> int:
    engine = get_engine()
    return await create_default_superuser(engine)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    code = asyncio.run(main())
    sys.exit(code)
