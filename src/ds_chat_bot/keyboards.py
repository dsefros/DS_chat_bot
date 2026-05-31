"""Telegram keyboard builders."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from ds_chat_bot.db.constants import CATEGORIES
from ds_chat_bot.callbacks import (
    DISCOVERY_CATEGORIES_CALLBACK,
    DISCOVERY_CATEGORY_PREFIX,
    DISCOVERY_LIKE_PREFIX,
    DISCOVERY_MENU_CALLBACK,
    DISCOVERY_SKIP_PREFIX,
)

MAIN_MENU_PROFILE_TEXT = "Заполнить / обновить анкету"
MAIN_MENU_MY_PROFILE_TEXT = "Моя анкета"
MAIN_MENU_PARTNER_SEARCH_TEXT = "Найти партнера"
MAIN_MENU_RANDOM_COFFEE_TEXT = "Random Coffee"
MAIN_MENU_TEXTS = {
    MAIN_MENU_PROFILE_TEXT,
    MAIN_MENU_MY_PROFILE_TEXT,
    MAIN_MENU_PARTNER_SEARCH_TEXT,
    MAIN_MENU_RANDOM_COFFEE_TEXT,
}

PROFILE_START_CALLBACK = "profile:start"
PROFILE_VIEW_CALLBACK = "profile:view"
PROFILE_EDIT_CALLBACK = "profile:update:edit"
PROFILE_RESTART_CALLBACK = "profile:update:restart"
CONNECT_MENU_CALLBACK = "menu:connect"
PARTNER_SEARCH_CALLBACK = "placeholder:partner_search"
RANDOM_COFFEE_CALLBACK = "placeholder:random_coffee"
SKIP_CALLBACK = "profile:skip"
CANCEL_CALLBACK = "profile:cancel"
PREVIEW_SUBMIT_CALLBACK = "profile:submit"
PREVIEW_RESTART_CALLBACK = "profile:restart"
ALLOW_CONTACT_YES_CALLBACK = "profile:allow_contact:yes"
ALLOW_CONTACT_NO_CALLBACK = "profile:allow_contact:no"
USERNAME_USE_DETECTED_CALLBACK = "profile:telegram_username:use_detected"
USERNAME_ENTER_MANUAL_CALLBACK = "profile:telegram_username:enter_manual"
ACTIVE_FORM_CONTINUE_CALLBACK = "profile:active:continue"
ACTIVE_FORM_CANCEL_TO_MENU_CALLBACK = "profile:active:cancel_to_menu"
CATEGORY_PREFIX = "profile:category:"
MODERATE_PREFIX = "moderate:"


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Build the persistent main navigation reply keyboard."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MAIN_MENU_PROFILE_TEXT), KeyboardButton(text=MAIN_MENU_MY_PROFILE_TEXT)],
            [KeyboardButton(text=MAIN_MENU_PARTNER_SEARCH_TEXT), KeyboardButton(text=MAIN_MENU_RANDOM_COFFEE_TEXT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def connect_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the inline /connect menu."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MAIN_MENU_PROFILE_TEXT, callback_data=PROFILE_START_CALLBACK)],
            [InlineKeyboardButton(text=MAIN_MENU_MY_PROFILE_TEXT, callback_data=PROFILE_VIEW_CALLBACK)],
            [InlineKeyboardButton(text=MAIN_MENU_PARTNER_SEARCH_TEXT, callback_data=PARTNER_SEARCH_CALLBACK)],
            [InlineKeyboardButton(text=MAIN_MENU_RANDOM_COFFEE_TEXT, callback_data=RANDOM_COFFEE_CALLBACK)],
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


def username_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, использовать", callback_data=USERNAME_USE_DETECTED_CALLBACK)],
            [InlineKeyboardButton(text="Указать другой", callback_data=USERNAME_ENTER_MANUAL_CALLBACK)],
            [InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)],
        ]
    )


def active_questionnaire_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить заполнение", callback_data=ACTIVE_FORM_CONTINUE_CALLBACK)],
            [InlineKeyboardButton(text="Отменить и открыть меню", callback_data=ACTIVE_FORM_CANCEL_TO_MENU_CALLBACK)],
        ]
    )


def profile_update_entry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить анкету", callback_data=PROFILE_EDIT_CALLBACK)],
            [InlineKeyboardButton(text="Заполнить заново", callback_data=PROFILE_RESTART_CALLBACK)],
            [InlineKeyboardButton(text=MAIN_MENU_MY_PROFILE_TEXT, callback_data=PROFILE_VIEW_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=CONNECT_MENU_CALLBACK)],
        ]
    )


def approval_navigation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MAIN_MENU_MY_PROFILE_TEXT, callback_data=PROFILE_VIEW_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=CONNECT_MENU_CALLBACK)],
        ]
    )


def rejection_navigation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить анкету", callback_data=PROFILE_EDIT_CALLBACK)],
            [InlineKeyboardButton(text=MAIN_MENU_MY_PROFILE_TEXT, callback_data=PROFILE_VIEW_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=CONNECT_MENU_CALLBACK)],
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
            [InlineKeyboardButton(text="Изменить анкету", callback_data=PROFILE_EDIT_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=CONNECT_MENU_CALLBACK)],
        ]
    )


def discovery_blocked_keyboard() -> InlineKeyboardMarkup:
    """Build navigation for users whose profile status blocks discovery."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MAIN_MENU_MY_PROFILE_TEXT, callback_data=PROFILE_VIEW_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=CONNECT_MENU_CALLBACK)],
        ]
    )


def discovery_categories_keyboard() -> InlineKeyboardMarkup:
    """Build category selection keyboard for partner discovery."""

    rows: list[list[InlineKeyboardButton]] = []
    for index in range(0, len(CATEGORIES), 2):
        rows.append(
            [
                InlineKeyboardButton(text=category, callback_data=f"{DISCOVERY_CATEGORY_PREFIX}{category}")
                for category in CATEGORIES[index : index + 2]
            ]
        )
    rows.append([InlineKeyboardButton(text="В меню", callback_data=DISCOVERY_MENU_CALLBACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def discovery_profile_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    """Build actions keyboard for a shown discovery profile card."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Интересно", callback_data=f"{DISCOVERY_LIKE_PREFIX}{profile_id}"),
                InlineKeyboardButton(text="Пропустить", callback_data=f"{DISCOVERY_SKIP_PREFIX}{profile_id}"),
            ],
            [InlineKeyboardButton(text="Другая категория", callback_data=DISCOVERY_CATEGORIES_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=DISCOVERY_MENU_CALLBACK)],
        ]
    )


def discovery_retry_keyboard() -> InlineKeyboardMarkup:
    """Build discovery fallback keyboard for no-more and stale states."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Другая категория", callback_data=DISCOVERY_CATEGORIES_CALLBACK)],
            [InlineKeyboardButton(text="В меню", callback_data=DISCOVERY_MENU_CALLBACK)],
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
