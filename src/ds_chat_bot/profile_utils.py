"""Validation and formatting helpers for participant profiles."""

from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING, Any, Mapping

from ds_chat_bot.db.constants import ProfileStatus

if TYPE_CHECKING:
    from ds_chat_bot.db.models import Profile

TELEGRAM_USERNAME_RE = re.compile(r"^@[A-Za-z0-9_]{5,32}$")

STATUS_LABELS: dict[str, str] = {
    ProfileStatus.DRAFT.value: "Черновик",
    ProfileStatus.PENDING_REVIEW.value: "На проверке",
    ProfileStatus.APPROVED.value: "Одобрена",
    ProfileStatus.REJECTED.value: "Отклонена",
    ProfileStatus.HIDDEN.value: "Скрыта",
}


def parse_optional_age(value: str) -> int | None:
    """Parse an optional age field, raising ValueError for non-integers."""

    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)


def is_valid_telegram_username(value: str) -> bool:
    """Validate a required @username in Telegram username format."""

    return bool(TELEGRAM_USERNAME_RE.fullmatch(value.strip()))


def _empty(value: object) -> str:
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _yes_no(value: bool) -> str:
    return "да" if value else "нет"


def format_profile_preview(data: Mapping[str, Any] | "Profile", *, include_status: bool = False) -> str:
    """Format a full participant profile preview for users and admins."""

    def get(name: str) -> Any:
        if isinstance(data, Mapping):
            return data.get(name)
        return getattr(data, name)

    lines = [
        f"Имя: {_empty(get('name'))}",
        f"Компания: {_empty(get('company'))}",
        f"Направление: {_empty(get('category'))}",
        f"Должность: {_empty(get('position'))}",
        f"Функционал: {_empty(get('function_description'))}",
        f"Задачи: {_empty(get('tasks_description'))}",
        f"Сайт: {_empty(get('company_site'))}",
        f"Увлечения: {_empty(get('hobbies'))}",
        f"Возраст: {_empty(get('age'))}",
        f"Город: {_empty(get('city'))}",
        f"Telegram: {_empty(get('telegram_username'))}",
        f"Показ контакта после интереса: {_yes_no(bool(get('allow_contact_reveal')))}",
    ]
    if include_status:
        status = str(get("status"))
        lines.append(f"Статус: {STATUS_LABELS.get(status, status)}")
    return "\n".join(lines)


def format_user_preview(data: Mapping[str, Any] | "Profile") -> str:
    """Format the confirmation preview shown before profile submission."""

    return f"Проверь свою анкету:\n\n{format_profile_preview(data)}\n\nВсё верно?"


def format_admin_review(profile: "Profile") -> str:
    """Format a moderation DM with Telegram and profile details."""

    telegram_username = profile.user.username if profile.user else None
    telegram_username = f"@{telegram_username}" if telegram_username else "—"
    return (
        "Новая анкета на проверку.\n\n"
        f"Telegram user id: {profile.user.telegram_id if profile.user else '—'}\n"
        f"Telegram username из Telegram: {telegram_username}\n"
        f"Profile ID: {profile.id}\n\n"
        f"{format_profile_preview(profile)}"
    )
