from typing import Any, Type

import colorful as cf
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql.ddl import DropTable, DDL

from app import models  # noqa: F401
from app.database.base import Base, PgBase, RdbBase


async def setup_db(engine: AsyncEngine, db_name: str):
    print(f"DROPPING ALL BASE TABLES IN {db_name} DATABASE")

    # await add_sequence_variant_projected_graph(engine, apache_age_conn)

    async with engine.begin() as conn:
        await conn.run_sync(drop_safe)

        print(f"Adding models to {db_name} database")

        await conn.run_sync(add_safe)

        if engine.name == "postgresql":
            await conn.run_sync(setup_pg)

            print_tables(Base, PgBase)
        elif engine.name == "sqlite":
            await conn.run_sync(setup_rdb)

            print_tables(Base, RdbBase)
        else:
            raise NotImplementedError(f"Unsupported database: {engine.name}")


def drop_safe(engine: AsyncEngine):
    engine.execute(
        DDL(
            """
            DROP MATERIALIZED VIEW IF EXISTS public.individual_variants_mv CASCADE;
            """
        )
    )

    engine.execute(
        DDL(
            """
            DROP MATERIALIZED VIEW IF EXISTS sequence_variant_connected_components_mv CASCADE;
            """
        )
    )

    Base.metadata.drop_all(
        engine,
        tables=get_tables(Base),
    )


def add_safe(engine: AsyncEngine):
    Base.metadata.create_all(
        engine,
        tables=get_tables(Base),
    )


def get_tables(base: Type[Base]) -> list[Table]:
    # return the list of tables to create/delete - only the ones not in the uta
    # schema
    return [
        table
        for table in base.metadata.tables.values()
        if table.schema != "uta"
    ]


def print_tables(base: Type[Base], other_base: Type[PgBase | RdbBase]):
    all_tables = list(base.metadata.tables.keys()) + list(
        other_base.metadata.tables.keys()
    )

    print(cf.green(f"Added tables: {all_tables} to database"))


def setup_pg(engine: AsyncEngine):
    tables = get_tables(PgBase)
    print("DROPPING ALL PG TABLES")
    PgBase.metadata.drop_all(engine, tables=tables)
    print("Adding models to pg database")
    PgBase.metadata.create_all(engine, tables=tables)


def setup_rdb(engine: AsyncEngine):
    print("DROPPING ALL RDB TABLES")
    RdbBase.metadata.drop_all(engine)
    print("Adding models to rdb database")
    RdbBase.metadata.create_all(engine)
