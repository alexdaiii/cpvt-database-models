from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable

import colorful as cf
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.types import AsyncSessionMaker


async def _issue_callback(
    session: AsyncSession,
    fn: Callable[[AsyncSession], Awaitable[None]] | None,
):
    if fn is not None:
        await fn(session)


@asynccontextmanager
async def _make_session(
    async_session: AsyncSessionMaker,
    *,
    setup_callback: Callable[[AsyncSession], Awaitable[None]] | None = None,
    teardown_callback: Callable[[AsyncSession], Awaitable[None]] | None = None,
):
    """
    This is a context manager that will automatically commit or rollback
    """
    async with async_session() as session:
        try:
            # issue command to enable type checking
            await _issue_callback(session, setup_callback)

            yield session
        except Exception as e:
            # cannot use 3.12 f strings bc of black error with mypy
            print(f"{cf.bold_red('An error occurred, rolling back')}")
            await session.rollback()
            raise
        finally:
            await _issue_callback(session, teardown_callback)
            await session.commit()


async def _sqlite_setup_callback(session: AsyncSession):
    await session.execute(text("PRAGMA foreign_keys=ON"))


@asynccontextmanager
async def get_session(
    async_session: AsyncSessionMaker,
) -> AsyncIterator[AsyncSession]:
    db_name = async_session.kw["bind"].dialect.name

    if db_name == "sqlite":
        async with _make_session(
            async_session, setup_callback=_sqlite_setup_callback
        ) as session:
            yield session
    elif db_name == "mysql" or db_name == "mariadb" or db_name == "postgresql":
        async with _make_session(async_session) as session:
            yield session

    else:
        raise NotImplementedError("Database not supported")


@asynccontextmanager
async def get_engine(
    dsn: str, *, echo: bool = False, n_conn: int
) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(dsn, echo=echo, pool_size=n_conn)

    try:
        yield engine
    finally:
        await engine.dispose()


@asynccontextmanager
async def get_sessionmaker(
    engine: AsyncEngine,
) -> AsyncIterator[AsyncSessionMaker]:
    async_session = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    yield async_session


__all__ = [
    "get_engine",
    "get_sessionmaker",
    "get_session",
]
