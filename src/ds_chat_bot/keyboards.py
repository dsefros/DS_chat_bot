"""Telegram keyboard builders."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

COMING_SOON_CALLBACK = "coming_soon"


def connect_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the placeholder main menu for the /connect command."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заполнить / обновить анкету", callback_data=COMING_SOON_CALLBACK)],
            [InlineKeyboardButton(text="Найти партнера", callback_data=COMING_SOON_CALLBACK)],
            [InlineKeyboardButton(text="Random Coffee", callback_data=COMING_SOON_CALLBACK)],
            [InlineKeyboardButton(text="Моя анкета", callback_data=COMING_SOON_CALLBACK)],
        ]
    )
