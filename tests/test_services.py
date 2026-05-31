import asyncio
from types import SimpleNamespace
from typing import Any

from ds_chat_bot.db.constants import ProfileStatus
from ds_chat_bot.db.models import User
from ds_chat_bot.services import (
    is_profile_moderation_decided,
    profile_status_label,
    upsert_user_from_telegram,
)


class _Result:
    def __init__(self, user: User | None) -> None:
        self._user = user

    def scalar_one_or_none(self) -> User | None:
        return self._user


class _FakeSession:
    def __init__(self, user: User | None = None) -> None:
        self.user = user
        self.added: list[User] = []
        self.committed = False
        self.refreshed: User | None = None

    async def execute(self, statement: Any) -> _Result:
        return _Result(self.user)

    def add(self, user: User) -> None:
        self.added.append(user)
        self.user = user

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, user: User) -> None:
        self.refreshed = user


def test_upsert_user_creates_new_user_without_blocking_flag_changes() -> None:
    async def run() -> None:
        session = _FakeSession()
        telegram_user = SimpleNamespace(
            id=123,
            username="anna",
            first_name="Анна",
            last_name="Иванова",
        )

        user = await upsert_user_from_telegram(session, telegram_user, (123,))

        assert user.telegram_id == 123
        assert user.username == "anna"
        assert user.first_name == "Анна"
        assert user.last_name == "Иванова"
        assert user.is_admin is True
        assert user.is_blocked is False
        assert session.added == [user]
        assert session.committed is True
        assert session.refreshed is user

    asyncio.run(run())


def test_upsert_user_updates_existing_user_but_preserves_is_blocked() -> None:
    async def run() -> None:
        existing = User(telegram_id=123, username="old", is_admin=False, is_blocked=True)
        session = _FakeSession(existing)
        telegram_user = SimpleNamespace(
            id=123,
            username="new",
            first_name="Новая",
            last_name=None,
        )

        user = await upsert_user_from_telegram(session, telegram_user, ())

        assert user is existing
        assert user.username == "new"
        assert user.first_name == "Новая"
        assert user.last_name is None
        assert user.is_admin is False
        assert user.is_blocked is True
        assert session.added == []
        assert session.committed is True
        assert session.refreshed is user

    asyncio.run(run())


def test_moderation_decision_helpers_are_idempotency_friendly() -> None:
    assert is_profile_moderation_decided(ProfileStatus.APPROVED.value) is True
    assert is_profile_moderation_decided(ProfileStatus.REJECTED.value) is True
    assert is_profile_moderation_decided(ProfileStatus.PENDING_REVIEW.value) is False
    assert profile_status_label(ProfileStatus.APPROVED.value) == "одобрена"
    assert profile_status_label(ProfileStatus.REJECTED.value) == "отклонена"
