"""
Alembic environment configuration for async SQLAlchemy (asyncpg).

Reads the database URL from ALEMBIC_DATABASE_URL or DATABASE_URL, and pulls
metadata from the application's declarative Base so `--autogenerate` works.
"""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------- #
# Make `backend.app` importable when alembic runs from the project root
# ---------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ---------------------------------------------------------------------- #
# Load .env so ALEMBIC_DATABASE_URL / DATABASE_URL are available
# ---------------------------------------------------------------------- #
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:  # python-dotenv is optional
    pass

# ---------------------------------------------------------------------- #
# Import application metadata
# ---------------------------------------------------------------------- #
# Adjust these imports to match your project layout. The two things we need
# are: (1) a SQLAlchemy 2.x `DeclarativeBase` subclass, and (2) a module that
# imports every model so autogenerate can see them.
from backend.app.db.base import Base  # noqa: E402  (DeclarativeBase subclass)
import backend.app.db.models  # noqa: E402,F401  (registers all models on Base.metadata)

# ---------------------------------------------------------------------- #
# Alembic Config object + logging
# ---------------------------------------------------------------------- #
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ---------------------------------------------------------------------- #
# Database URL resolution
# ---------------------------------------------------------------------- #
def get_database_url() -> str:
    """
    Priority order:
      1. ALEMBIC_DATABASE_URL (explicit override for migrations)
      2. DATABASE_URL        (shared app URL)
      3. sqlalchemy.url      (from alembic.ini, if someone hard-coded it)
    """
    url = (
        os.getenv("ALEMBIC_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
    )
    if not url:
        raise RuntimeError(
            "No database URL configured. Set ALEMBIC_DATABASE_URL or "
            "DATABASE_URL in your environment / .env file."
        )
    return url


# ---------------------------------------------------------------------- #
# Offline mode — emit SQL to stdout without a live DB connection
# ---------------------------------------------------------------------- #
def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=True,  # harmless on Postgres, helpful on SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------- #
# Online mode — sync wrapper that drives the async engine
# ---------------------------------------------------------------------- #
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {}) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # migrations shouldn't reuse pooled conns
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------- #
# Entry point
# ---------------------------------------------------------------------- #
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()