"""Telegram command, text, and callback handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ds_chat_bot.config import Settings
from ds_chat_bot.keyboards import (
    MAIN_MENU_MY_PROFILE_TEXT,
    MAIN_MENU_PARTNER_SEARCH_TEXT,
    MAIN_MENU_PROFILE_TEXT,
    MAIN_MENU_RANDOM_COFFEE_TEXT,
    PARTNER_SEARCH_CALLBACK,
    RANDOM_COFFEE_CALLBACK,
    active_questionnaire_keyboard,
    main_reply_keyboard,
)
from ds_chat_bot.profile_handlers import (
    is_questionnaire_state,
    router as profile_router,
    send_profile_update_entry,
    send_profile_view,
)
from ds_chat_bot.services import upsert_user_from_telegram

router = Router(name="main")

START_TEXT = """Привет! Это бот сообщества «Давай сконнектимся».

Здесь можно заполнить анкету участника и отправить её на проверку администратору.

Выбери действие в меню ниже."""

CONNECT_TEXT = "Что хочешь сделать?"
COMING_SOON_TEXT = "Этот раздел появится в следующей версии MVP."
HEALTH_TEXT = "Бот работает."


async def send_connect_menu(message: Message) -> None:
    """Send the main menu using only the persistent reply keyboard."""

    await message.answer(CONNECT_TEXT, reply_markup=main_reply_keyboard())


async def _show_active_questionnaire_guard(message: Message) -> None:
    await message.answer(
        "Ты сейчас заполняешь анкету. Что сделать?",
        reply_markup=active_questionnaire_keyboard(),
    )


async def _show_active_questionnaire_callback_guard(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Ты сейчас заполняешь анкету. Что сделать?",
            reply_markup=active_questionnaire_keyboard(),
        )


@router.message(Command("start"))
async def handle_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    """Upsert the user and send intro or deep-linked connect menu."""

    await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_guard(message)
        return
    if (command.args or "").strip().lower() == "connect":
        await send_connect_menu(message)
        return
    await message.answer(START_TEXT, reply_markup=main_reply_keyboard())


@router.message(Command("connect", ignore_case=True))
async def handle_connect(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    """Upsert the user and send the main menu."""

    await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_guard(message)
        return
    await send_connect_menu(message)


@router.message(Command("health"))
async def handle_health(message: Message) -> None:
    """Lightweight command for checking that the bot process responds."""

    await message.answer(HEALTH_TEXT, reply_markup=main_reply_keyboard())


@router.message(F.text == MAIN_MENU_PROFILE_TEXT)
async def handle_profile_menu_text(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_guard(message)
        return
    user = await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    await send_profile_update_entry(message, user.id, db_session, state)


@router.message(F.text == MAIN_MENU_MY_PROFILE_TEXT)
async def handle_my_profile_menu_text(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_guard(message)
        return
    user = await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    await send_profile_view(message, user.id, db_session)


@router.message(F.text.in_({MAIN_MENU_PARTNER_SEARCH_TEXT, MAIN_MENU_RANDOM_COFFEE_TEXT}))
async def handle_placeholder_menu_text(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_guard(message)
        return
    await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    await message.answer(COMING_SOON_TEXT, reply_markup=main_reply_keyboard())


@router.callback_query(F.data.in_({PARTNER_SEARCH_CALLBACK, RANDOM_COFFEE_CALLBACK}))
async def handle_coming_soon(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    """Acknowledge future MVP menu actions without implementing discovery/coffee."""

    await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_callback_guard(callback)
        return
    await callback.answer()
    if callback.message:
        await callback.message.answer(COMING_SOON_TEXT, reply_markup=main_reply_keyboard())


router.include_router(profile_router)
