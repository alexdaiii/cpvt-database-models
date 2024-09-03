import asyncio
import os
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from cpvt_database_models.settings import get_settings

_ERROR_MESSAGE = (
    "The cpvt_database_models add_views file requires that sqlparse and "
    "the pydantic-settings libraries are installed.  In order to ensure these "
    "are installed, please run the following commands:\n"
    "'pip install cpvt_database_models[add_views] cpvt_database_models[with_settings] --index-url https://gitlab.com/api/v4/projects/60969577/packages/pypi/simple'\n"
    "You will also need to have an async postgres driver installed such "
    "as psycopg or asyncpg."
)


def get_sql_files(base_dir: str):
    """
    Sql files should be located in the ./sql directory relative to this file
    """

    sql_files = []

    for root, _, files in os.walk(base_dir):
        for file in sorted(files):
            if file.endswith(".sql"):
                sql_files.append(os.path.join(root, file))

    return sql_files


async def add_views_pg(session: AsyncSession, base_dir: str):
    print("Adding views")

    sql_files = get_sql_files(base_dir)

    print(f"Found {len(sql_files)} sql files")

    for sql_file in sql_files:
        print(f"Executing {sql_file}")
        await execute_file(session, sql_file)

    await session.commit()


async def execute_file(session: AsyncSession, sql_file):
    try:
        import sqlparse
    except ImportError as e:
        raise ImportError(_ERROR_MESSAGE) from e

    # start a timer
    start_time = time.time()

    with open(sql_file, "r") as f:
        sql = f.read()

        for stmt in sqlparse.split(sql):
            print(f"Executing: \n{stmt}")
            await session.execute(text(stmt))

    # end the timer
    end_time = time.time()

    print(f"Time taken: {end_time - start_time:.2f} seconds")


async def add_views_main():  # pragma: no cover
    asyncio_engine = create_async_engine(get_settings().postgresql_dsn)
    base_dir = os.path.join(os.path.dirname(__file__), "sql")

    async with asyncio_engine.begin() as conn:
        await add_views_pg(conn, base_dir)


if __name__ == "__main__":
    asyncio.run(add_views_main())

__all__ = ["add_views_pg", "add_views_main"]
