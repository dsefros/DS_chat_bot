"""Profile questionnaire, preview, and admin moderation handlers."""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ds_chat_bot.config import Settings
from ds_chat_bot.db.constants import CATEGORIES, ProfileStatus
from ds_chat_bot.keyboards import (
    ALLOW_CONTACT_NO_CALLBACK,
    ALLOW_CONTACT_YES_CALLBACK,
    CANCEL_CALLBACK,
    CATEGORY_PREFIX,
    CONNECT_MENU_CALLBACK,
    MODERATE_PREFIX,
    PREVIEW_RESTART_CALLBACK,
    PREVIEW_SUBMIT_CALLBACK,
    PROFILE_START_CALLBACK,
    PROFILE_VIEW_CALLBACK,
    SKIP_CALLBACK,
    allow_contact_keyboard,
    cancel_keyboard,
    categories_keyboard,
    existing_profile_keyboard,
    moderation_keyboard,
    no_profile_keyboard,
    preview_keyboard,
    skip_cancel_keyboard,
)
from ds_chat_bot.profile_utils import (
    STATUS_LABELS,
    format_admin_review,
    format_profile_preview,
    format_user_preview,
    is_valid_telegram_username,
    parse_optional_age,
)
from ds_chat_bot.services import (
    get_profile_for_user,
    get_profile_with_user,
    is_admin_telegram_id,
    save_profile_for_review,
    set_profile_status,
    upsert_user_from_telegram,
)

logger = logging.getLogger(__name__)
router = Router(name="profiles")

OPTIONAL_FIELDS = {"company_site", "hobbies", "age", "city"}


def _message_text(message: Message) -> str:
    return (message.text or "").strip()


async def _require_text(message: Message, prompt: str) -> str | None:
    value = _message_text(message)
    if value:
        return value
    await message.answer(
        f"Это обязательное поле. Напиши ответ текстом.\n\n{prompt}",
        reply_markup=cancel_keyboard(),
    )
    return None


class ProfileForm(StatesGroup):
    name = State()
    company = State()
    category = State()
    position = State()
    function_description = State()
    tasks_description = State()
    company_site = State()
    hobbies = State()
    age = State()
    city = State()
    telegram_username = State()
    allow_contact_reveal = State()
    preview = State()


async def _upsert_current_user(
    event: Message | CallbackQuery,
    db_session: AsyncSession,
    settings: Settings,
):
    return await upsert_user_from_telegram(
        db_session,
        event.from_user,
        settings.admin_telegram_ids,
    )


async def start_questionnaire(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProfileForm.name)
    await message.answer("Как тебя зовут?", reply_markup=cancel_keyboard())


async def send_profile_view(message: Message, user_id: int, db_session: AsyncSession) -> None:
    profile = await get_profile_for_user(db_session, user_id)
    if profile is None:
        await message.answer(
            "У тебя пока нет анкеты.\n"
            "Заполни её, чтобы другие участники могли понять, чем ты занимаешься.",
            reply_markup=no_profile_keyboard(),
        )
        return

    await message.answer(
        f"Твоя анкета:\n\n{format_profile_preview(profile, include_status=True)}",
        reply_markup=existing_profile_keyboard(),
    )


async def notify_admins(bot: Bot, settings: Settings, profile_id: int, db_session: AsyncSession) -> None:
    profile = await get_profile_with_user(db_session, profile_id)
    if profile is None:
        logger.warning("admin_notification_skipped profile_id=%s reason=missing", profile_id)
        return

    text = format_admin_review(profile)
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=moderation_keyboard(profile.id))
        except Exception as exc:  # noqa: BLE001 - Telegram DM failures must not break user flow.
            logger.warning(
                "admin_notification_failed admin_id=%s profile_id=%s error=%r",
                admin_id,
                profile.id,
                exc,
            )


@router.message(Command("edit_profile"))
async def handle_edit_profile_command(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    await _upsert_current_user(message, db_session, settings)
    await start_questionnaire(message, state)


@router.message(Command("profile"))
async def handle_profile_command(
    message: Message,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await _upsert_current_user(message, db_session, settings)
    await send_profile_view(message, user.id, db_session)


@router.message(Command("cancel"))
async def handle_cancel_command(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    await _upsert_current_user(message, db_session, settings)
    await state.clear()
    await message.answer("Заполнение анкеты отменено.")


@router.callback_query(F.data == PROFILE_START_CALLBACK)
async def handle_profile_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    await _upsert_current_user(callback, db_session, settings)
    await callback.answer()
    if callback.message:
        await start_questionnaire(callback.message, state)


@router.callback_query(F.data == PROFILE_VIEW_CALLBACK)
async def handle_profile_view_callback(
    callback: CallbackQuery,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await _upsert_current_user(callback, db_session, settings)
    await callback.answer()
    if callback.message:
        await send_profile_view(callback.message, user.id, db_session)


@router.callback_query(F.data == CONNECT_MENU_CALLBACK)
async def handle_connect_menu_callback(
    callback: CallbackQuery,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    from ds_chat_bot.handlers import send_connect_menu

    await _upsert_current_user(callback, db_session, settings)
    await callback.answer()
    if callback.message:
        await send_connect_menu(callback.message)


@router.callback_query(F.data == CANCEL_CALLBACK)
async def handle_cancel_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    await _upsert_current_user(callback, db_session, settings)
    await state.clear()
    await callback.answer("Отменено")
    if callback.message:
        await callback.message.answer("Заполнение анкеты отменено.")


@router.message(ProfileForm.name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = await _require_text(message, "Как тебя зовут?")
    if name is None:
        return
    await state.update_data(name=name)
    await state.set_state(ProfileForm.company)
    await message.answer("Из какой ты компании?", reply_markup=cancel_keyboard())


@router.message(ProfileForm.company)
async def process_company(message: Message, state: FSMContext) -> None:
    company = await _require_text(message, "Из какой ты компании?")
    if company is None:
        return
    await state.update_data(company=company)
    await state.set_state(ProfileForm.category)
    await message.answer("Выбери своё направление:", reply_markup=categories_keyboard())


@router.callback_query(ProfileForm.category, F.data.startswith(CATEGORY_PREFIX))
async def process_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.removeprefix(CATEGORY_PREFIX)
    if category not in CATEGORIES:
        await callback.answer("Выбери направление из списка.", show_alert=True)
        return
    await state.update_data(category=category)
    await state.set_state(ProfileForm.position)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Какая у тебя должность?", reply_markup=cancel_keyboard())


@router.message(ProfileForm.position)
async def process_position(message: Message, state: FSMContext) -> None:
    position = await _require_text(message, "Какая у тебя должность?")
    if position is None:
        return
    await state.update_data(position=position)
    await state.set_state(ProfileForm.function_description)
    await message.answer("Какой у тебя функционал? За что отвечаешь?", reply_markup=cancel_keyboard())


@router.message(ProfileForm.function_description)
async def process_function_description(message: Message, state: FSMContext) -> None:
    function_description = await _require_text(
        message,
        "Какой у тебя функционал? За что отвечаешь?",
    )
    if function_description is None:
        return
    await state.update_data(function_description=function_description)
    await state.set_state(ProfileForm.tasks_description)
    await message.answer("Какие задачи решаешь в отделе?", reply_markup=cancel_keyboard())


@router.message(ProfileForm.tasks_description)
async def process_tasks_description(message: Message, state: FSMContext) -> None:
    tasks_description = await _require_text(message, "Какие задачи решаешь в отделе?")
    if tasks_description is None:
        return
    await state.update_data(tasks_description=tasks_description)
    await state.set_state(ProfileForm.company_site)
    await message.answer(
        "Укажи сайт компании. Если сайта нет или не хочешь указывать — нажми «Пропустить».",
        reply_markup=skip_cancel_keyboard(),
    )


async def _store_optional_and_advance(
    state: FSMContext,
    message: Message,
    field: str,
    value: Any,
) -> None:
    await state.update_data(**{field: value})
    if field == "company_site":
        await state.set_state(ProfileForm.hobbies)
        await message.answer(
            "Напиши свои увлечения. Это поможет другим участникам проще начать диалог. Можно пропустить.",
            reply_markup=skip_cancel_keyboard(),
        )
    elif field == "hobbies":
        await state.set_state(ProfileForm.age)
        await message.answer("Сколько тебе лет? Можно пропустить.", reply_markup=skip_cancel_keyboard())
    elif field == "age":
        await state.set_state(ProfileForm.city)
        await message.answer("Твой город? Можно пропустить.", reply_markup=skip_cancel_keyboard())
    elif field == "city":
        await state.set_state(ProfileForm.telegram_username)
        await message.answer("Напиши свой ник в Telegram в формате @username.", reply_markup=cancel_keyboard())


@router.callback_query(F.data == SKIP_CALLBACK)
async def handle_skip(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    field = current_state.rsplit(":", 1)[-1] if current_state else ""
    if field not in OPTIONAL_FIELDS:
        await callback.answer("Это поле нельзя пропустить.", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await _store_optional_and_advance(state, callback.message, field, None)


@router.message(ProfileForm.company_site)
async def process_company_site(message: Message, state: FSMContext) -> None:
    await _store_optional_and_advance(state, message, "company_site", _message_text(message))


@router.message(ProfileForm.hobbies)
async def process_hobbies(message: Message, state: FSMContext) -> None:
    await _store_optional_and_advance(state, message, "hobbies", _message_text(message))


@router.message(ProfileForm.age)
async def process_age(message: Message, state: FSMContext) -> None:
    try:
        age = parse_optional_age(message.text or "")
    except ValueError:
        await message.answer(
            "Возраст должен быть целым числом. Введи возраст или нажми «Пропустить».",
            reply_markup=skip_cancel_keyboard(),
        )
        return
    await _store_optional_and_advance(state, message, "age", age)


@router.message(ProfileForm.city)
async def process_city(message: Message, state: FSMContext) -> None:
    await _store_optional_and_advance(state, message, "city", _message_text(message))


@router.message(ProfileForm.telegram_username)
async def process_telegram_username(message: Message, state: FSMContext) -> None:
    username = _message_text(message)
    if not is_valid_telegram_username(username):
        await message.answer(
            "Ник должен начинаться с @ и содержать 5–32 символа: латинские буквы, цифры или подчёркивание.",
            reply_markup=cancel_keyboard(),
        )
        return
    await state.update_data(telegram_username=username)
    await state.set_state(ProfileForm.allow_contact_reveal)
    await message.answer(
        "Разрешаешь показывать твой Telegram-ник участникам, которые нажмут «Интересно» на твоей анкете?",
        reply_markup=allow_contact_keyboard(),
    )


@router.callback_query(
    ProfileForm.allow_contact_reveal,
    F.data.in_({ALLOW_CONTACT_YES_CALLBACK, ALLOW_CONTACT_NO_CALLBACK}),
)
async def process_allow_contact(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(allow_contact_reveal=callback.data == ALLOW_CONTACT_YES_CALLBACK)
    data = await state.get_data()
    await state.set_state(ProfileForm.preview)
    await callback.answer()
    if callback.message:
        await callback.message.answer(format_user_preview(data), reply_markup=preview_keyboard())


@router.callback_query(ProfileForm.preview, F.data == PREVIEW_RESTART_CALLBACK)
async def process_preview_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await start_questionnaire(callback.message, state)


@router.callback_query(ProfileForm.preview, F.data == PREVIEW_SUBMIT_CALLBACK)
async def process_preview_submit(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await _upsert_current_user(callback, db_session, settings)
    data = await state.get_data()
    profile = await save_profile_for_review(db_session, user.id, data)
    await state.clear()
    await callback.answer("Отправлено на проверку")
    if callback.message:
        await callback.message.answer(
            "Анкета отправлена на проверку.\n"
            "После одобрения администратором она появится в разделе «Найти партнера»."
        )
    await notify_admins(bot, settings, profile.id, db_session)


@router.callback_query(F.data.startswith(MODERATE_PREFIX))
async def handle_moderation_callback(
    callback: CallbackQuery,
    bot: Bot,
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    await _upsert_current_user(callback, db_session, settings)
    if not is_admin_telegram_id(callback.from_user.id, settings.admin_telegram_ids):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    try:
        _, action, raw_profile_id = callback.data.split(":", 2)
        profile_id = int(raw_profile_id)
    except (AttributeError, ValueError):
        await callback.answer("Некорректная команда модерации.", show_alert=True)
        return

    profile = await get_profile_with_user(db_session, profile_id)
    if profile is None:
        await callback.answer("Анкета не найдена.", show_alert=True)
        return

    if profile.status in {ProfileStatus.APPROVED.value, ProfileStatus.REJECTED.value}:
        label = STATUS_LABELS.get(profile.status, profile.status)
        await callback.answer(f"Анкета уже имеет статус: {label}.", show_alert=True)
        return

    if action == "approve":
        await set_profile_status(db_session, profile, ProfileStatus.APPROVED)
        try:
            await bot.send_message(
                profile.user.telegram_id,
                "Анкета одобрена.\n"
                "Теперь тебя смогут найти другие участники в разделе «Найти партнера».",
            )
        except Exception as exc:  # noqa: BLE001 - owner may have blocked the bot.
            logger.warning(
                "profile_owner_notification_failed profile_id=%s user_id=%s error=%r",
                profile.id,
                profile.user.telegram_id,
                exc,
            )
        await callback.answer("Анкета одобрена.")
        if callback.message:
            await callback.message.answer(f"Анкета #{profile.id} одобрена.")
    elif action == "reject":
        await set_profile_status(db_session, profile, ProfileStatus.REJECTED)
        try:
            await bot.send_message(
                profile.user.telegram_id,
                "Анкета не прошла проверку.\n"
                "Ты можешь отредактировать её и отправить на проверку повторно через /connect.",
            )
        except Exception as exc:  # noqa: BLE001 - owner may have blocked the bot.
            logger.warning(
                "profile_owner_notification_failed profile_id=%s user_id=%s error=%r",
                profile.id,
                profile.user.telegram_id,
                exc,
            )
        await callback.answer("Анкета отклонена.")
        if callback.message:
            await callback.message.answer(f"Анкета #{profile.id} отклонена.")
    else:
        await callback.answer("Неизвестное действие.", show_alert=True)
