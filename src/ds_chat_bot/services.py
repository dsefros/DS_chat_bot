"""Small database service functions used by Telegram handlers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ds_chat_bot.db.base import utc_now
from ds_chat_bot.db.constants import ProfileStatus
from ds_chat_bot.db.models import Profile, User


def is_admin_telegram_id(telegram_id: int, admin_ids: tuple[int, ...]) -> bool:
    """Return whether a Telegram ID belongs to a configured bot admin."""

    return telegram_id in admin_ids


def is_profile_moderation_decided(status: str) -> bool:
    """Return whether a profile moderation decision is already final."""

    return status in {ProfileStatus.APPROVED.value, ProfileStatus.REJECTED.value}


def profile_status_label(status: str) -> str:
    """Return a human-readable moderation status label for callback answers."""

    labels = {
        ProfileStatus.APPROVED.value: "одобрена",
        ProfileStatus.REJECTED.value: "отклонена",
        ProfileStatus.PENDING_REVIEW.value: "на проверке",
        ProfileStatus.DRAFT.value: "черновик",
        ProfileStatus.HIDDEN.value: "скрыта",
    }
    return labels.get(status, status)


async def upsert_user_from_telegram(
    session: AsyncSession,
    telegram_user: Any,
    admin_ids: tuple[int, ...],
) -> User:
    """Create or update a Telegram user by telegram_id without changing block state."""

    result = await session.execute(
        select(User).where(User.telegram_id == telegram_user.id)
    )
    user = result.scalar_one_or_none()
    now = utc_now()
    is_admin = is_admin_telegram_id(int(telegram_user.id), admin_ids)

    if user is None:
        user = User(
            telegram_id=int(telegram_user.id),
            username=getattr(telegram_user, "username", None),
            first_name=getattr(telegram_user, "first_name", None),
            last_name=getattr(telegram_user, "last_name", None),
            is_admin=is_admin,
            is_blocked=False,
            updated_at=now,
        )
        session.add(user)
    else:
        user.username = getattr(telegram_user, "username", None)
        user.first_name = getattr(telegram_user, "first_name", None)
        user.last_name = getattr(telegram_user, "last_name", None)
        user.is_admin = is_admin
        user.updated_at = now

    await session.commit()
    await session.refresh(user)
    return user


async def get_profile_for_user(session: AsyncSession, user_id: int) -> Profile | None:
    """Return the participant profile for an internal user ID, if any."""

    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def save_profile_for_review(
    session: AsyncSession,
    user_id: int,
    data: dict[str, Any],
) -> Profile:
    """Create or update a profile and submit it to manual admin premoderation."""

    profile = await get_profile_for_user(session, user_id)
    now = utc_now()
    values = {
        "name": data["name"],
        "company": data["company"],
        "category": data["category"],
        "position": data["position"],
        "function_description": data["function_description"],
        "tasks_description": data["tasks_description"],
        "company_site": data.get("company_site"),
        "hobbies": data.get("hobbies"),
        "age": data.get("age"),
        "city": data.get("city"),
        "telegram_username": data["telegram_username"],
        "allow_contact_reveal": bool(data["allow_contact_reveal"]),
        "status": ProfileStatus.PENDING_REVIEW.value,
        "updated_at": now,
    }

    if profile is None:
        profile = Profile(user_id=user_id, **values)
        session.add(profile)
    else:
        for field, value in values.items():
            setattr(profile, field, value)

    await session.commit()
    await session.refresh(profile)
    return profile


async def get_profile_with_user(session: AsyncSession, profile_id: int) -> Profile | None:
    """Return a profile with its owner for moderation actions."""

    result = await session.execute(
        select(Profile)
        .options(selectinload(Profile.user))
        .where(Profile.id == profile_id)
    )
    return result.scalar_one_or_none()


async def set_profile_status(
    session: AsyncSession,
    profile: Profile,
    status: ProfileStatus,
) -> Profile:
    """Set a profile status and persist the moderation decision."""

    profile.status = status.value
    profile.updated_at = utc_now()
    await session.commit()
    await session.refresh(profile)
    return profile
