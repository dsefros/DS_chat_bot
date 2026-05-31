import pytest

from ds_chat_bot.db.constants import CATEGORIES, PROFILE_STATUSES, ProfileStatus
from ds_chat_bot.profile_utils import (
    format_detected_telegram_username,
    format_profile_preview,
    is_valid_telegram_username,
    parse_optional_age,
    stale_callback_message,
)
from ds_chat_bot.services import is_admin_telegram_id


def test_admin_id_detection_uses_numeric_ids() -> None:
    assert is_admin_telegram_id(111, (111, 222)) is True
    assert is_admin_telegram_id(333, (111, 222)) is False


def test_format_detected_telegram_username_adds_prefix_and_validates() -> None:
    assert format_detected_telegram_username("ann_acme") == "@ann_acme"
    assert format_detected_telegram_username("@ann_acme") == "@ann_acme"
    assert format_detected_telegram_username(None) is None
    assert format_detected_telegram_username("abcd") is None
    assert format_detected_telegram_username("ann-acme") is None


def test_stale_callback_message_points_to_menu() -> None:
    assert stale_callback_message() == "Открой меню и выбери нужное действие."


@pytest.mark.parametrize("value", ["@abcde", "@abc_123", "@A2345", "@" + "a" * 32])
def test_valid_telegram_username(value: str) -> None:
    assert is_valid_telegram_username(value) is True


@pytest.mark.parametrize("value", ["abcde", "@abcd", "@abc-de", "@абвгд", "@" + "a" * 33])
def test_invalid_telegram_username(value: str) -> None:
    assert is_valid_telegram_username(value) is False


def test_parse_optional_age_accepts_blank_and_integer() -> None:
    assert parse_optional_age("") is None
    assert parse_optional_age(" 42 ") == 42


def test_parse_optional_age_rejects_non_integer() -> None:
    with pytest.raises(ValueError):
        parse_optional_age("сорок")


def test_profile_preview_formats_all_required_fields() -> None:
    preview = format_profile_preview(
        {
            "name": "Анна",
            "company": "ACME",
            "category": CATEGORIES[0],
            "position": "CMO",
            "function_description": "Маркетинг",
            "tasks_description": "Рост",
            "company_site": None,
            "hobbies": "Бег",
            "age": 30,
            "city": "Москва",
            "telegram_username": "@ann_acme",
            "allow_contact_reveal": True,
            "status": ProfileStatus.PENDING_REVIEW.value,
        },
        include_status=True,
    )

    assert "Имя: Анна" in preview
    assert "Сайт: —" in preview
    assert "Показ контакта после интереса: да" in preview
    assert "Статус: На проверке" in preview


def test_profile_statuses_include_moderation_states() -> None:
    assert ProfileStatus.PENDING_REVIEW.value in PROFILE_STATUSES
    assert ProfileStatus.APPROVED.value in PROFILE_STATUSES
    assert ProfileStatus.REJECTED.value in PROFILE_STATUSES
