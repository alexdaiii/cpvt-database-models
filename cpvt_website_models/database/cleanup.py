from sqlalchemy import Engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.database.db import get_session, get_sessionmaker
from app.database.types import AsyncSessionMaker


async def reset_sequences_to_max(
    db: AsyncSessionMaker,
    table_name: str,
    sequence_name: str,
    primary_key: str,
):
    async with get_session(db) as session:
        # Set the sequence value to the maximum value of the primary key
        await session.execute(
            text(
                f"SELECT setval('{sequence_name}', (SELECT MAX({primary_key}) FROM {table_name}));"
            )
        )


async def cleanup_sequences(engine: AsyncEngine):
    tables_to_reset = await get_primary_keys_and_sequences(engine)

    async with get_sessionmaker(engine) as db:
        for table_name, sequence_name, primary_key in tables_to_reset:
            await reset_sequences_to_max(
                db, table_name, sequence_name, primary_key
            )


async def get_primary_keys_and_sequences(engine: AsyncEngine):
    tables_to_reset: list[tuple[str, str, str]] = []

    def _get_primary_keys_and_sequences(sync_eng: Engine):
        inspector = inspect(sync_eng)

        sequences = set(inspector.get_sequence_names())
        print(f"Sequence Names: {sequences}")

        for table_name in inspector.get_table_names():
            primary_keys = inspector.get_pk_constraint(table_name)[
                "constrained_columns"
            ]

            # check if there is a sequence for the primary key
            if len(primary_keys) != 1:
                # multi primary key reset not supported
                continue

            primary_key = primary_keys[0]
            # check to sequence exists - should be in the format
            # (table_name)_(primary_key)_seq
            sequence_name = f"{table_name}_{primary_key}_seq"

            if sequence_name not in sequences:
                continue

            print(
                f"Resetting primary key sequence for {table_name}, "
                f"{primary_key}, {sequence_name}"
            )

            tables_to_reset.append((table_name, sequence_name, primary_key))

    async with engine.begin() as conn:
        await conn.run_sync(_get_primary_keys_and_sequences)

    return tables_to_reset
