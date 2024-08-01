from typing import NewType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

AsyncSessionMaker = NewType(
    "AsyncSessionMaker", async_sessionmaker[AsyncSession]
)
