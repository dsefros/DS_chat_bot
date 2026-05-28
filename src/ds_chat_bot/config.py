"""Environment-based application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


class SettingsError(RuntimeError):
    """Raised when required application settings are missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    bot_token: str
    admin_telegram_ids: tuple[int, ...]
    main_chat_id: int
    timezone: str
    database_url: str
    log_level: str


def _get_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SettingsError(f"Missing required environment variable: {name}")
    return value


def _parse_int(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise SettingsError(f"Environment variable {name} must be an integer") from exc


def _parse_admin_ids(value: str) -> tuple[int, ...]:
    ids = [item.strip() for item in value.split(",") if item.strip()]
    if not ids:
        raise SettingsError("Environment variable ADMIN_TELEGRAM_IDS must contain at least one Telegram ID")

    parsed_ids: list[int] = []
    for item in ids:
        try:
            parsed_ids.append(int(item))
        except ValueError as exc:
            raise SettingsError("Environment variable ADMIN_TELEGRAM_IDS must be a comma-separated list of integers") from exc
    return tuple(parsed_ids)


def load_settings() -> Settings:
    """Load and validate settings from process environment variables."""

    admin_ids = _parse_admin_ids(_get_required("ADMIN_TELEGRAM_IDS"))
    main_chat_id = _parse_int("MAIN_CHAT_ID", _get_required("MAIN_CHAT_ID"))

    return Settings(
        bot_token=_get_required("BOT_TOKEN"),
        admin_telegram_ids=admin_ids,
        main_chat_id=main_chat_id,
        timezone=os.getenv("TIMEZONE", "Europe/Moscow").strip() or "Europe/Moscow",
        database_url=_get_required("DATABASE_URL"),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )
