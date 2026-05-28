"""Telegram command and callback handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ds_chat_bot.keyboards import COMING_SOON_CALLBACK, connect_menu_keyboard

router = Router(name="main")

START_TEXT = """Привет! Это бот сообщества «Давай сконнектимся».

Здесь позже можно будет заполнить анкету, найти полезные контакты и участвовать в Random Coffee.

Чтобы открыть меню, используй команду /connect."""

CONNECT_TEXT = """Что хочешь сделать?

• Заполнить / обновить анкету
• Найти партнера
• Random Coffee
• Моя анкета"""

COMING_SOON_TEXT = "Этот раздел появится в следующей версии MVP."
HEALTH_TEXT = "Бот работает."


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Send the introductory community bot message."""

    await message.answer(START_TEXT)


@router.message(Command("connect"))
async def handle_connect(message: Message) -> None:
    """Send the placeholder main menu."""

    await message.answer(CONNECT_TEXT, reply_markup=connect_menu_keyboard())


@router.message(Command("health"))
async def handle_health(message: Message) -> None:
    """Lightweight command for checking that the bot process responds."""

    await message.answer(HEALTH_TEXT)


@router.callback_query(lambda callback: callback.data == COMING_SOON_CALLBACK)
async def handle_coming_soon(callback: CallbackQuery) -> None:
    """Acknowledge placeholder menu actions without implementing MVP features."""

    await callback.answer()
    if callback.message:
        await callback.message.answer(COMING_SOON_TEXT)
