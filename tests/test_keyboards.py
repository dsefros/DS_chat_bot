from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from ds_chat_bot.keyboards import (
    MAIN_MENU_MY_PROFILE_TEXT,
    MAIN_MENU_PARTNER_SEARCH_TEXT,
    MAIN_MENU_PROFILE_TEXT,
    MAIN_MENU_RANDOM_COFFEE_TEXT,
    active_questionnaire_keyboard,
    discovery_blocked_keyboard,
    main_reply_keyboard,
    profile_update_entry_keyboard,
    username_confirmation_keyboard,
)


def test_persistent_main_reply_keyboard_exists() -> None:
    keyboard = main_reply_keyboard()

    assert isinstance(keyboard, ReplyKeyboardMarkup)
    texts = {button.text for row in keyboard.keyboard for button in row}
    assert texts == {
        MAIN_MENU_PROFILE_TEXT,
        MAIN_MENU_MY_PROFILE_TEXT,
        MAIN_MENU_PARTNER_SEARCH_TEXT,
        MAIN_MENU_RANDOM_COFFEE_TEXT,
    }
    assert keyboard.is_persistent is True


def test_active_questionnaire_decision_keyboard_exists() -> None:
    keyboard = active_questionnaire_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    texts = [button.text for row in keyboard.inline_keyboard for button in row]
    assert texts == ["Продолжить заполнение", "Отменить и открыть меню"]


def test_username_confirmation_keyboard_has_required_choices() -> None:
    texts = [button.text for row in username_confirmation_keyboard().inline_keyboard for button in row]

    assert texts == ["Да, использовать", "Указать другой", "Отмена"]


def test_profile_update_entry_keyboard_has_required_choices() -> None:
    texts = [button.text for row in profile_update_entry_keyboard().inline_keyboard for button in row]

    assert texts == ["Изменить анкету", "Заполнить заново", "Моя анкета", "В меню"]


def test_discovery_blocked_keyboard_has_profile_and_menu_navigation() -> None:
    keyboard = discovery_blocked_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    texts = [button.text for row in keyboard.inline_keyboard for button in row]
    assert texts == ["Моя анкета", "В меню"]
