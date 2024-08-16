import asyncio
from contextlib import asynccontextmanager
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
)

from alembic import context

#
# from app_v2 import models  # noqa: F401, F403


from cpvt_website_models.database.base import Base
from cpvt_website_models.settings import get_settings
from cpvt_website_models import models  # noqa: F401, F403

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

exclude_table_schema = {"uta"}

excluded_tables = {
    table.name
    for table in target_metadata.tables.values()
    if table.schema in exclude_table_schema
}


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_settings().postgresql_dsn.__str__()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name not in excluded_tables

    return True


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


@asynccontextmanager
async def get_async_engine() -> AsyncEngine:
    connectable = create_async_engine(
        get_settings().postgresql_dsn.__str__(),
        echo=False,
        poolclass=pool.NullPool,
    )

    async with connectable.begin() as conn:
        try:
            yield conn

            await conn.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await conn.close()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # connectable = async_engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )
    async with get_async_engine() as connection:
        await connection.run_sync(do_run_migrations)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
