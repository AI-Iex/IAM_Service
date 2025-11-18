from __future__ import with_statement
import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from alembic import context
from app.core.config import settings
from app.db.base import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging (only if config file exists)
if config.config_file_name:
    fileConfig(config.config_file_name)

# Add app directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in online mode."""

    url = config.get_main_option("sqlalchemy.url")
    if url:
        # Called programmatically with explicit URL
        connectable = create_engine(url, poolclass=pool.NullPool)
    else:
        # Called via CLI with alembic.ini
        connectable = engine_from_config(
            config.get_section(config.config_ini_section) or {},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
