import pytest
import pytest_asyncio
from sqlalchemy import text, Connection
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    AsyncConnection,
    async_sessionmaker,
)


@pytest.fixture(scope="module")
def get_container() -> PostgresContainer:
    with PostgresContainer("postgres:16", driver="psycopg_async") as postgres:
        print(
            f"Successfully started postgres container: {postgres.get_connection_url()}"
        )
        yield postgres


@pytest.fixture(scope="module")
def get_engine(get_container: PostgresContainer) -> AsyncEngine:
    asyncio_engine = create_async_engine(get_container.get_connection_url(), echo=True)

    yield asyncio_engine


@pytest_asyncio.fixture()
async def get_conn(get_engine: AsyncEngine) -> AsyncSession:
    """This session fixture wraps every test in a transaction

    This session fixture will rollback the transaction after every function.
    Note that this will NOT rollback any sequences, such as the id sequence.
    This is the intended behavior and a feature of transaction in Postgres.
    """
    async with get_engine.connect() as conn:
        async with conn.begin() as tx:
            try:
                yield conn
            finally:
                await tx.rollback()


@pytest_asyncio.fixture()
async def setup_session(get_conn: AsyncConnection) -> AsyncConnection:
    """
    Sets up the database with the models (Runs every time a test is run)
    """

    def _add_models(_conn: Connection):
        from cpvt_website_models import models  # noqa: F401
        from cpvt_website_models.database import BaseBase

        # create the uta schema
        _conn.execute(text("CREATE SCHEMA IF NOT EXISTS uta;"))

        BaseBase.metadata.create_all(
            _conn,
        )

    # add the CITEXT extension
    await get_conn.execute(
        text(
            """
            CREATE EXTENSION IF NOT EXISTS citext;
            """
        )
    )
    await get_conn.run_sync(_add_models)

    print("Successfully added models to the database")

    yield get_conn


@pytest_asyncio.fixture()
async def session(setup_session: AsyncConnection) -> AsyncSession:
    session_maker = async_sessionmaker(
        setup_session, expire_on_commit=False, class_=AsyncSession
    )
    async with session_maker() as sess:
        yield sess
