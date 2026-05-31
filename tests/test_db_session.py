import asyncio

import pytest

from ds_chat_bot.db.session import DbSessionMiddleware


class _FakeSession:
    def __init__(self) -> None:
        self.rolled_back = False

    async def rollback(self) -> None:
        self.rolled_back = True


class _FakeSessionContext:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> _FakeSession:
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _FakeSessionFactory:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    def __call__(self) -> _FakeSessionContext:
        return _FakeSessionContext(self.session)


def test_db_session_middleware_rolls_back_and_reraises_handler_errors() -> None:
    async def run() -> None:
        session = _FakeSession()
        middleware = DbSessionMiddleware(_FakeSessionFactory(session))

        async def handler(event, data):  # noqa: ANN001
            assert data["db_session"] is session
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await middleware(handler, object(), {})

        assert session.rolled_back is True

    asyncio.run(run())


def test_db_session_middleware_does_not_rollback_successful_handlers() -> None:
    async def run() -> None:
        session = _FakeSession()
        middleware = DbSessionMiddleware(_FakeSessionFactory(session))

        async def handler(event, data):  # noqa: ANN001
            assert data["db_session"] is session
            return "ok"

        assert await middleware(handler, object(), {}) == "ok"
        assert session.rolled_back is False

    asyncio.run(run())
