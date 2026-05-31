"""Telegram command, text, and callback handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ds_chat_bot.config import Settings
from ds_chat_bot.callbacks import (
    DISCOVERY_CATEGORIES_CALLBACK,
    DISCOVERY_CATEGORY_PREFIX,
    DISCOVERY_LIKE_PREFIX,
    DISCOVERY_MENU_CALLBACK,
    DISCOVERY_SKIP_PREFIX,
)
from ds_chat_bot.discovery import (
    DISCOVERY_CATEGORY_PROMPT,
    DISCOVERY_RESELECT_TEXT,
    DISCOVERY_STALE_TEXT,
    can_user_use_discovery,
    format_discovery_profile_card,
    get_discovery_candidate_by_id,
    get_next_discovery_profile,
    no_more_profiles_message,
    parse_discovery_category_callback,
    parse_discovery_profile_callback,
    record_contact_reveal,
    record_like,
    record_profile_view,
    record_skip,
    safe_remove_inline_keyboard,
    user_has_terminal_profile_view,
)
from ds_chat_bot.db.constants import ProfileViewAction
from ds_chat_bot.keyboards import (
    MAIN_MENU_MY_PROFILE_TEXT,
    MAIN_MENU_PARTNER_SEARCH_TEXT,
    MAIN_MENU_PROFILE_TEXT,
    MAIN_MENU_RANDOM_COFFEE_TEXT,
    PARTNER_SEARCH_CALLBACK,
    RANDOM_COFFEE_CALLBACK,
    active_questionnaire_keyboard,
    discovery_blocked_keyboard,
    discovery_categories_keyboard,
    discovery_profile_keyboard,
    discovery_retry_keyboard,
    main_reply_keyboard,
    no_profile_keyboard,
    rejection_navigation_keyboard,
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


@router.message(F.text == MAIN_MENU_RANDOM_COFFEE_TEXT)
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


@router.callback_query(F.data == RANDOM_COFFEE_CALLBACK)
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


async def _send_discovery_access_denied(message: Message, reason: str) -> None:
    if reason == "missing_profile":
        await message.answer(
            "Чтобы искать партнеров, сначала заполни анкету.",
            reply_markup=main_reply_keyboard(),
        )
        await message.answer("Что сделать?", reply_markup=no_profile_keyboard())
        return
    if reason == "pending_review":
        await message.answer(
            "Твоя анкета пока на проверке. После одобрения ты сможешь искать партнеров.",
            reply_markup=main_reply_keyboard(),
        )
        await message.answer("Что сделать?", reply_markup=discovery_blocked_keyboard())
        return
    if reason == "rejected":
        await message.answer(
            "Твоя анкета не прошла проверку. Измени её и отправь на проверку повторно.",
            reply_markup=main_reply_keyboard(),
        )
        await message.answer("Что сделать?", reply_markup=rejection_navigation_keyboard())
        return
    await message.answer(
        "Поиск партнеров доступен только после одобрения анкеты.",
        reply_markup=main_reply_keyboard(),
    )
    await message.answer("Что сделать?", reply_markup=discovery_blocked_keyboard())


async def _send_discovery_categories(message: Message) -> None:
    await message.answer(
        DISCOVERY_CATEGORY_PROMPT,
        reply_markup=discovery_categories_keyboard(),
    )


async def _send_no_more_profiles(message: Message) -> None:
    await message.answer(
        no_more_profiles_message(),
        reply_markup=main_reply_keyboard(),
    )
    await message.answer("Что сделать?", reply_markup=discovery_retry_keyboard())


async def _send_stale_discovery_fallback(message: Message) -> None:
    await message.answer(DISCOVERY_STALE_TEXT, reply_markup=main_reply_keyboard())
    await message.answer(DISCOVERY_RESELECT_TEXT, reply_markup=discovery_retry_keyboard())


async def _show_next_discovery_profile(
    message: Message,
    db_session: AsyncSession,
    viewer_user_id: int,
    category: str,
) -> None:
    profile = await get_next_discovery_profile(db_session, viewer_user_id, category)
    if profile is None:
        await _send_no_more_profiles(message)
        return
    await record_profile_view(
        db_session,
        viewer_user_id,
        profile.id,
        ProfileViewAction.VIEWED,
        category,
    )
    await message.answer(
        format_discovery_profile_card(profile),
        reply_markup=discovery_profile_keyboard(profile.id),
    )


async def _start_discovery_for_user(message: Message, user_id: int, db_session: AsyncSession) -> None:
    access = await can_user_use_discovery(db_session, user_id)
    if not access.allowed:
        await _send_discovery_access_denied(message, access.reason)
        return
    await _send_discovery_categories(message)


@router.message(F.text == MAIN_MENU_PARTNER_SEARCH_TEXT)
@router.message(Command("find_partner"))
async def handle_partner_search_text(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await upsert_user_from_telegram(db_session, message.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_guard(message)
        return
    await _start_discovery_for_user(message, user.id, db_session)


@router.callback_query(F.data == PARTNER_SEARCH_CALLBACK)
async def handle_partner_search_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_callback_guard(callback)
        return
    await callback.answer()
    if callback.message:
        await _start_discovery_for_user(callback.message, user.id, db_session)


@router.callback_query(F.data == DISCOVERY_CATEGORIES_CALLBACK)
async def handle_discovery_categories_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_callback_guard(callback)
        return
    await callback.answer()
    await safe_remove_inline_keyboard(callback)
    if callback.message:
        access = await can_user_use_discovery(db_session, user.id)
        if not access.allowed:
            await _send_discovery_access_denied(callback.message, access.reason)
            return
        await _send_discovery_categories(callback.message)


@router.callback_query(F.data.startswith(DISCOVERY_CATEGORY_PREFIX))
async def handle_discovery_category_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_callback_guard(callback)
        return
    category = parse_discovery_category_callback(callback.data)
    await callback.answer()
    await safe_remove_inline_keyboard(callback)
    if callback.message is None:
        return
    access = await can_user_use_discovery(db_session, user.id)
    if not access.allowed:
        await _send_discovery_access_denied(callback.message, access.reason)
        return
    if category is None:
        await _send_stale_discovery_fallback(callback.message)
        return
    await _show_next_discovery_profile(callback.message, db_session, user.id, category)


@router.callback_query(F.data.startswith(DISCOVERY_LIKE_PREFIX))
async def handle_discovery_like_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_callback_guard(callback)
        return
    await callback.answer()
    await safe_remove_inline_keyboard(callback)
    if callback.message is None:
        return
    access = await can_user_use_discovery(db_session, user.id)
    if not access.allowed:
        await _send_discovery_access_denied(callback.message, access.reason)
        return
    profile_id = parse_discovery_profile_callback(callback.data, DISCOVERY_LIKE_PREFIX)
    if profile_id is None:
        await _send_stale_discovery_fallback(callback.message)
        return
    candidate = await get_discovery_candidate_by_id(db_session, profile_id)
    if candidate is None or candidate.user_id == user.id or await user_has_terminal_profile_view(db_session, user.id, profile_id):
        await _send_stale_discovery_fallback(callback.message)
        return
    category = candidate.category
    if await record_like(db_session, user.id, candidate.id, category) is None:
        await _send_stale_discovery_fallback(callback.message)
        return
    if candidate.allow_contact_reveal:
        await callback.message.answer(
            f"Контакт открыт: {candidate.telegram_username}\n\nМожешь написать и договориться о встрече.",
            reply_markup=main_reply_keyboard(),
        )
        await record_contact_reveal(db_session, user.id, candidate.id, category)
    else:
        await callback.message.answer(
            "Участник пока не разрешил показывать Telegram-ник.",
            reply_markup=main_reply_keyboard(),
        )
    await _show_next_discovery_profile(callback.message, db_session, user.id, category)


@router.callback_query(F.data.startswith(DISCOVERY_SKIP_PREFIX))
async def handle_discovery_skip_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_callback_guard(callback)
        return
    await callback.answer()
    await safe_remove_inline_keyboard(callback)
    if callback.message is None:
        return
    access = await can_user_use_discovery(db_session, user.id)
    if not access.allowed:
        await _send_discovery_access_denied(callback.message, access.reason)
        return
    profile_id = parse_discovery_profile_callback(callback.data, DISCOVERY_SKIP_PREFIX)
    if profile_id is None:
        await _send_stale_discovery_fallback(callback.message)
        return
    candidate = await get_discovery_candidate_by_id(db_session, profile_id)
    if candidate is None or candidate.user_id == user.id or await user_has_terminal_profile_view(db_session, user.id, profile_id):
        await _send_stale_discovery_fallback(callback.message)
        return
    category = candidate.category
    if await record_skip(db_session, user.id, candidate.id, category) is None:
        await _send_stale_discovery_fallback(callback.message)
        return
    await _show_next_discovery_profile(callback.message, db_session, user.id, category)


@router.callback_query(F.data == DISCOVERY_MENU_CALLBACK)
async def handle_discovery_menu_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    await upsert_user_from_telegram(db_session, callback.from_user, settings.admin_telegram_ids)
    if is_questionnaire_state(await state.get_state()):
        await _show_active_questionnaire_callback_guard(callback)
        return
    await callback.answer()
    await safe_remove_inline_keyboard(callback)
    if callback.message:
        await send_connect_menu(callback.message)


router.include_router(profile_router)
