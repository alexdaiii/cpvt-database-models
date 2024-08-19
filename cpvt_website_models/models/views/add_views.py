import asyncio
import os
import time

import sqlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from cpvt_website_models.settings import get_settings


def get_sql_files():
    """
    Sql files should be located in the ./sql directory relative to this file
    """

    sql_files = []

    for root, _, files in os.walk(
            os.path.join(os.path.dirname(__file__), "sql")):
        for file in sorted(files):
            if file.endswith(".sql"):
                sql_files.append(os.path.join(root, file))

    return sql_files


async def add_views_pg(session: AsyncSession):
    print("Adding views")

    sql_files = get_sql_files()

    for sql_file in sql_files:
        print(f"Executing {sql_file}")
        await execute_file(session, sql_file)

    await session.commit()


async def execute_file(session: AsyncSession, sql_file):
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


async def main():
    asyncio_engine = create_async_engine(get_settings().postgresql_dsn)

    async with asyncio_engine.begin() as conn:
        await add_views_pg(conn)


if __name__ == "__main__":
    asyncio.run(main())

__all__ = ["add_views_pg", "main"]
