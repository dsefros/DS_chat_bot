import pytest

from ds_chat_bot.config import SettingsError, load_settings


REQUIRED_ENV = {
    "BOT_TOKEN": "123456:test-token",
    "ADMIN_TELEGRAM_IDS": "111,222",
    "MAIN_CHAT_ID": "-1001234567890",
    "DATABASE_URL": "postgresql+asyncpg://ds_bot:ds_bot_password@postgres:5432/ds_bot",
}


def set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)


def test_load_settings_parses_required_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.setenv("TIMEZONE", "Europe/Moscow")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = load_settings()

    assert settings.bot_token == "123456:test-token"
    assert settings.admin_telegram_ids == (111, 222)
    assert settings.main_chat_id == -1001234567890
    assert settings.timezone == "Europe/Moscow"
    assert settings.database_url == REQUIRED_ENV["DATABASE_URL"]
    assert settings.log_level == "DEBUG"


def test_load_settings_fails_when_required_value_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.delenv("BOT_TOKEN")

    with pytest.raises(SettingsError, match="BOT_TOKEN"):
        load_settings()


def test_load_settings_fails_when_admin_ids_are_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    set_required_env(monkeypatch)
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "not-an-id")

    with pytest.raises(SettingsError, match="ADMIN_TELEGRAM_IDS"):
        load_settings()
