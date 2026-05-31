import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.types import ReplyKeyboardMarkup

from ds_chat_bot import handlers


def run(coro):
    return asyncio.run(coro)


def make_message() -> SimpleNamespace:
    return SimpleNamespace(
        from_user=SimpleNamespace(id=123),
        answer=AsyncMock(),
    )


def make_state(current_state: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(get_state=AsyncMock(return_value=current_state))


def make_settings() -> SimpleNamespace:
    return SimpleNamespace(admin_telegram_ids=set())


def assert_single_reply_keyboard_answer(message: SimpleNamespace, text: str) -> None:
    message.answer.assert_awaited_once()
    args, kwargs = message.answer.await_args
    assert args == (text,)
    assert isinstance(kwargs["reply_markup"], ReplyKeyboardMarkup)


def test_send_connect_menu_uses_only_persistent_reply_keyboard() -> None:
    message = make_message()

    run(handlers.send_connect_menu(message))

    assert_single_reply_keyboard_answer(message, handlers.CONNECT_TEXT)


def test_start_without_deeplink_sends_only_greeting_with_reply_keyboard(monkeypatch) -> None:
    message = make_message()
    state = make_state()
    monkeypatch.setattr(handlers, "upsert_user_from_telegram", AsyncMock())

    run(
        handlers.handle_start(
            message=message,
            command=SimpleNamespace(args=None),
            state=state,
            db_session=SimpleNamespace(),
            settings=make_settings(),
        )
    )

    assert_single_reply_keyboard_answer(message, handlers.START_TEXT)


def test_start_connect_deeplink_matches_connect_reply_keyboard_only(monkeypatch) -> None:
    message = make_message()
    state = make_state()
    monkeypatch.setattr(handlers, "upsert_user_from_telegram", AsyncMock())

    run(
        handlers.handle_start(
            message=message,
            command=SimpleNamespace(args="connect"),
            state=state,
            db_session=SimpleNamespace(),
            settings=make_settings(),
        )
    )

    assert_single_reply_keyboard_answer(message, handlers.CONNECT_TEXT)


def test_connect_sends_only_persistent_reply_keyboard(monkeypatch) -> None:
    message = make_message()
    state = make_state()
    monkeypatch.setattr(handlers, "upsert_user_from_telegram", AsyncMock())

    run(
        handlers.handle_connect(
            message=message,
            state=state,
            db_session=SimpleNamespace(),
            settings=make_settings(),
        )
    )

    assert_single_reply_keyboard_answer(message, handlers.CONNECT_TEXT)
