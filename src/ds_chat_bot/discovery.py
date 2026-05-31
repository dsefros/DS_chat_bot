"""Partner discovery helpers and persistence functions."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ds_chat_bot.callbacks import DISCOVERY_CATEGORY_PREFIX
from ds_chat_bot.db.constants import CATEGORIES, ProfileStatus, ProfileViewAction
from ds_chat_bot.db.models import Profile, ProfileView, User

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery


DISCOVERY_CATEGORY_PROMPT = "Выбери направление, в котором хочешь найти партнера:"
DISCOVERY_NO_PROFILES_TEXT = "Упс, анкеты закончились!\nВыбери другую категорию или загляни попозже."
DISCOVERY_STALE_TEXT = "Эта карточка уже неактуальна."
DISCOVERY_RESELECT_TEXT = "Выбери категорию заново."

DiscoveryAccessReason = Literal[
    "approved",
    "missing_profile",
    "pending_review",
    "rejected",
    "not_approved",
]


@dataclass(frozen=True)
class DiscoveryAccess:
    """Result of checking whether a user may browse discovery."""

    allowed: bool
    reason: DiscoveryAccessReason
    profile: Profile | None = None


def is_profile_approved_for_discovery(profile: Any | None) -> bool:
    """Return whether a profile status allows partner discovery."""

    return bool(profile) and getattr(profile, "status", None) == ProfileStatus.APPROVED.value


def discovery_access_for_profile(profile: Profile | None) -> DiscoveryAccess:
    """Describe partner discovery access for a possibly missing own profile."""

    if profile is None:
        return DiscoveryAccess(False, "missing_profile")
    if profile.status == ProfileStatus.APPROVED.value:
        return DiscoveryAccess(True, "approved", profile)
    if profile.status == ProfileStatus.PENDING_REVIEW.value:
        return DiscoveryAccess(False, "pending_review", profile)
    if profile.status == ProfileStatus.REJECTED.value:
        return DiscoveryAccess(False, "rejected", profile)
    return DiscoveryAccess(False, "not_approved", profile)


def parse_discovery_category_callback(callback_data: str | None) -> str | None:
    """Extract a category from a discovery category callback."""

    if not callback_data or not callback_data.startswith(DISCOVERY_CATEGORY_PREFIX):
        return None
    category = callback_data.removeprefix(DISCOVERY_CATEGORY_PREFIX)
    if category not in CATEGORIES:
        return None
    return category


def parse_discovery_profile_callback(callback_data: str | None, prefix: str) -> int | None:
    """Extract a profile id from a like/skip callback."""

    if not callback_data or not callback_data.startswith(prefix):
        return None
    raw_profile_id = callback_data.removeprefix(prefix)
    try:
        profile_id = int(raw_profile_id)
    except ValueError:
        return None
    return profile_id if profile_id > 0 else None


def _empty(value: object) -> str:
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def format_discovery_profile_card(profile: Profile) -> str:
    """Format a discovery card without exposing private/internal fields."""

    return (
        "Анкета участника\n\n"
        f"Имя: {_empty(profile.name)}\n"
        f"Компания: {_empty(profile.company)}\n"
        f"Направление: {_empty(profile.category)}\n"
        f"Должность: {_empty(profile.position)}\n"
        f"Город: {_empty(profile.city)}\n\n"
        "Функционал:\n"
        f"{_empty(profile.function_description)}\n\n"
        "Какие задачи решает:\n"
        f"{_empty(profile.tasks_description)}\n\n"
        "Увлечения:\n"
        f"{_empty(profile.hobbies)}"
    )


def no_more_profiles_message() -> str:
    """Return the no-more-candidates message for discovery."""

    return DISCOVERY_NO_PROFILES_TEXT


async def get_approved_profile_for_user(session: AsyncSession, user_id: int) -> Profile | None:
    """Return user's profile only when it is approved for discovery."""

    result = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status == ProfileStatus.APPROVED.value,
        )
    )
    return result.scalar_one_or_none()


async def can_user_use_discovery(session: AsyncSession, user_id: int) -> DiscoveryAccess:
    """Load user's own profile and return discovery access details."""

    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    return discovery_access_for_profile(result.scalar_one_or_none())


async def user_has_terminal_profile_view(
    session: AsyncSession,
    viewer_user_id: int,
    profile_id: int,
) -> bool:
    """Return whether viewer already liked or skipped a candidate profile."""

    result = await session.execute(
        select(
            exists().where(
                ProfileView.viewer_user_id == viewer_user_id,
                ProfileView.profile_id == profile_id,
                ProfileView.action.in_(
                    [ProfileViewAction.LIKED.value, ProfileViewAction.SKIPPED.value]
                ),
            )
        )
    )
    return bool(result.scalar())


async def get_next_discovery_profile(
    session: AsyncSession,
    viewer_user_id: int,
    category: str,
) -> Profile | None:
    """Return the next approved candidate in category not liked/skipped by viewer."""

    terminal_view_exists = (
        select(ProfileView.id)
        .where(
            ProfileView.viewer_user_id == viewer_user_id,
            ProfileView.profile_id == Profile.id,
            ProfileView.action.in_([ProfileViewAction.LIKED.value, ProfileViewAction.SKIPPED.value]),
        )
        .exists()
    )
    result = await session.execute(
        select(Profile)
        .join(Profile.user)
        .options(selectinload(Profile.user))
        .where(
            Profile.status == ProfileStatus.APPROVED.value,
            Profile.category == category,
            Profile.user_id != viewer_user_id,
            User.is_blocked.is_(False),
            ~terminal_view_exists,
        )
        .order_by(Profile.updated_at.desc(), Profile.id.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_discovery_candidate_by_id(session: AsyncSession, profile_id: int) -> Profile | None:
    """Return an approved discovery candidate by id with its owner loaded."""

    result = await session.execute(
        select(Profile)
        .options(selectinload(Profile.user))
        .where(Profile.id == profile_id, Profile.status == ProfileStatus.APPROVED.value)
    )
    profile = result.scalar_one_or_none()
    if profile is None or profile.user is None or profile.user.is_blocked:
        return None
    return profile


async def record_profile_view(
    session: AsyncSession,
    viewer_user_id: int,
    profile_id: int,
    action: ProfileViewAction,
    category: str | None = None,
) -> ProfileView | None:
    """Record a discovery event and ignore duplicate terminal-action races."""

    view = ProfileView(
        viewer_user_id=viewer_user_id,
        profile_id=profile_id,
        action=action.value,
        category=category,
    )
    session.add(view)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return None
    await session.refresh(view)
    return view


async def record_like(
    session: AsyncSession,
    viewer_user_id: int,
    profile_id: int,
    category: str | None = None,
) -> ProfileView | None:
    return await record_profile_view(session, viewer_user_id, profile_id, ProfileViewAction.LIKED, category)


async def record_skip(
    session: AsyncSession,
    viewer_user_id: int,
    profile_id: int,
    category: str | None = None,
) -> ProfileView | None:
    return await record_profile_view(session, viewer_user_id, profile_id, ProfileViewAction.SKIPPED, category)


async def record_contact_reveal(
    session: AsyncSession,
    viewer_user_id: int,
    profile_id: int,
    category: str | None = None,
) -> ProfileView | None:
    return await record_profile_view(
        session,
        viewer_user_id,
        profile_id,
        ProfileViewAction.CONTACT_REVEALED,
        category,
    )


async def safe_remove_inline_keyboard(callback: "CallbackQuery") -> None:
    """Remove a used inline keyboard, ignoring Telegram edit failures."""

    if not callback.message:
        return
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:  # noqa: BLE001 - old Telegram messages may be immutable.
        return
