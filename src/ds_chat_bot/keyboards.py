"""Telegram keyboard builders."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ds_chat_bot.db.constants import CATEGORIES

PROFILE_START_CALLBACK = "profile:start"
PROFILE_VIEW_CALLBACK = "profile:view"
CONNECT_MENU_CALLBACK = "menu:connect"
PARTNER_SEARCH_CALLBACK = "placeholder:partner_search"
RANDOM_COFFEE_CALLBACK = "placeholder:random_coffee"
SKIP_CALLBACK = "profile:skip"
CANCEL_CALLBACK = "profile:cancel"
PREVIEW_SUBMIT_CALLBACK = "profile:submit"
PREVIEW_RESTART_CALLBACK = "profile:restart"
ALLOW_CONTACT_YES_CALLBACK = "profile:allow_contact:yes"
ALLOW_CONTACT_NO_CALLBACK = "profile:allow_contact:no"
CATEGORY_PREFIX = "profile:category:"
MODERATE_PREFIX = "moderate:"


def connect_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main menu for the /connect command."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заполнить / обновить анкету", callback_data=PROFILE_START_CALLBACK)],
            [InlineKeyboardButton(text="Найти партнера", callback_data=PARTNER_SEARCH_CALLBACK)],
            [InlineKeyboardButton(text="Random Coffee", callback_data=RANDOM_COFFEE_CALLBACK)],
            [InlineKeyboardButton(text="Моя анкета", callback_data=PROFILE_VIEW_CALLBACK)],
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)]]
    )


def skip_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data=SKIP_CALLBACK)],
            [InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)],
        ]
    )


def categories_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index in range(0, len(CATEGORIES), 2):
        rows.append(
            [
                InlineKeyboardButton(text=category, callback_data=f"{CATEGORY_PREFIX}{category}")
                for category in CATEGORIES[index : index + 2]
            ]
        )
    rows.append([InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def allow_contact_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, разрешаю", callback_data=ALLOW_CONTACT_YES_CALLBACK)],
            [InlineKeyboardButton(text="Нет, не разрешаю", callback_data=ALLOW_CONTACT_NO_CALLBACK)],
            [InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)],
        ]
    )


def preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Всё верно, отправить на проверку", callback_data=PREVIEW_SUBMIT_CALLBACK)],
            [InlineKeyboardButton(text="Заполнить заново", callback_data=PREVIEW_RESTART_CALLBACK)],
            [InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)],
        ]
    )


def no_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заполнить анкету", callback_data=PROFILE_START_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=CONNECT_MENU_CALLBACK)],
        ]
    )


def existing_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить анкету", callback_data=PROFILE_START_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=CONNECT_MENU_CALLBACK)],
        ]
    )


def moderation_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Одобрить", callback_data=f"{MODERATE_PREFIX}approve:{profile_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"{MODERATE_PREFIX}reject:{profile_id}"),
            ]
        ]
    )
