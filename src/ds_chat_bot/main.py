"""Application entry point for long-polling Telegram bot startup."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from ds_chat_bot.config import SettingsError, load_settings
from ds_chat_bot.db.session import (
    DbSessionMiddleware,
    create_engine,
    create_session_factory,
)
from ds_chat_bot.handlers import router

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configure concise structured logging for local and container runs."""

    logging.basicConfig(
        level=level,
        format="time=%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s",
    )


def create_bot_commands() -> list[BotCommand]:
    """Build the public Telegram command list registered for the bot."""

    return [
        BotCommand(command="start", description="старт"),
        BotCommand(command="connect", description="меню"),
        BotCommand(command="profile", description="моя анкета"),
        BotCommand(command="edit_profile", description="изменить анкету"),
        BotCommand(command="find_partner", description="найти партнера"),
        BotCommand(command="cancel", description="отменить текущее действие"),
    ]


async def run_bot() -> None:
    """Load settings and start the bot in long polling mode."""

    settings = load_settings()
    configure_logging(settings.log_level)

    logger.info(
        "bot_starting mode=long_polling timezone=%s main_chat_id=%s admins_count=%s",
        settings.timezone,
        settings.main_chat_id,
        len(settings.admin_telegram_ids),
    )

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.update.middleware(DbSessionMiddleware(session_factory))
    dispatcher.include_router(router)

    await bot.set_my_commands(create_bot_commands())

    logger.info("bot_running mode=long_polling")
    try:
        await dispatcher.start_polling(bot, settings=settings)
    finally:
        await engine.dispose()
        await bot.session.close()


def main() -> None:
    """Synchronous console entry point with fail-fast configuration errors."""

    try:
        asyncio.run(run_bot())
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
