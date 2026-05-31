"""Telegram command and callback handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ds_chat_bot.config import Settings
from ds_chat_bot.keyboards import (
    PARTNER_SEARCH_CALLBACK,
    RANDOM_COFFEE_CALLBACK,
    connect_menu_keyboard,
)
from ds_chat_bot.profile_handlers import router as profile_router
from ds_chat_bot.services import upsert_user_from_telegram

router = Router(name="main")

START_TEXT = """Привет! Это бот сообщества «Давай сконнектимся».

Здесь можно заполнить анкету участника и отправить её на проверку администратору.

Чтобы открыть меню, используй команду /connect или /Connect."""

CONNECT_TEXT = """Что хочешь сделать?

• Заполнить / обновить анкету
• Найти партнера
• Random Coffee
• Моя анкета"""

COMING_SOON_TEXT = "Этот раздел появится в следующей версии MVP."
HEALTH_TEXT = "Бот работает."


async def send_connect_menu(message: Message) -> None:
    """Send the main /connect menu."""

    await message.answer(CONNECT_TEXT, reply_markup=connect_menu_keyboard())


@router.message(Command("start"))
async def handle_start(
    message: Message,
    command: CommandObject,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    """Upsert the user and send intro or deep-linked connect menu."""

    await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    if (command.args or "").strip().lower() == "connect":
        await send_connect_menu(message)
        return
    await message.answer(START_TEXT)


@router.message(Command("connect", ignore_case=True))
async def handle_connect(
    message: Message,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    """Upsert the user and send the main menu."""

    await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    await send_connect_menu(message)


@router.message(Command("health"))
async def handle_health(message: Message) -> None:
    """Lightweight command for checking that the bot process responds."""

    await message.answer(HEALTH_TEXT)


@router.callback_query(F.data.in_({PARTNER_SEARCH_CALLBACK, RANDOM_COFFEE_CALLBACK}))
async def handle_coming_soon(
    callback: CallbackQuery,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    """Acknowledge future MVP menu actions without implementing discovery/coffee."""

    await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    await callback.answer()
    if callback.message:
        await callback.message.answer(COMING_SOON_TEXT)


router.include_router(profile_router)
