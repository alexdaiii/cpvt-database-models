import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from cpvt_database_models.models.views import add_views_pg
from cpvt_database_models.settings import get_settings


async def add_filters_main():  # pragma: no cover
    asyncio_engine = create_async_engine(get_settings().postgresql_dsn)
    base_dir = os.path.join(os.path.dirname(__file__), "sql")

    async with asyncio_engine.begin() as conn:
        await add_views_pg(conn, base_dir)


if __name__ == "__main__":
    asyncio.run(add_filters_main())

__all__ = ["add_filters_main"]
