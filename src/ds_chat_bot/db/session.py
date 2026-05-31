"""Runtime SQLAlchemy async engine and session helpers."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


def create_engine(database_url: str) -> AsyncEngine:
    """Create the runtime async SQLAlchemy engine without touching the schema."""

    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for request-scoped bot handlers."""

    return async_sessionmaker(engine, expire_on_commit=False)


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Backward-compatible alias for creating an async session factory."""

    return create_session_factory(engine)


@asynccontextmanager
async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield an async database session and close it afterwards."""

    async with session_factory() as session:
        yield session


class DbSessionMiddleware(BaseMiddleware):
    """Provide a fresh AsyncSession to every aiogram update handler."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self._session_factory() as session:
            data["db_session"] = session
            try:
                return await handler(event, data)
            except Exception:
                try:
                    await session.rollback()
                except Exception as rollback_exc:  # noqa: BLE001 - preserve original handler error.
                    logger.warning("db_session_rollback_failed error=%r", rollback_exc)
                raise
