"""Database-backed MVP constants."""

from __future__ import annotations

from enum import StrEnum


class ProfileStatus(StrEnum):
    """Lifecycle statuses for participant profiles."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    HIDDEN = "hidden"


class ProfileViewAction(StrEnum):
    """Actions a user can take while discovering profiles."""

    VIEWED = "viewed"
    LIKED = "liked"
    SKIPPED = "skipped"
    CONTACT_REVEALED = "contact_revealed"


class RandomCoffeeRoundStatus(StrEnum):
    """Lifecycle statuses for weekly Random Coffee rounds."""

    DRAFT = "draft"
    POLLING = "polling"
    PAIRED = "paired"
    CANCELLED = "cancelled"


class RandomCoffeeAnswerValue(StrEnum):
    """Allowed answers for Random Coffee weekly polls."""

    YES = "yes"
    NO = "no"


CATEGORIES: tuple[str, ...] = (
    "Партнерка",
    "Маркетинг",
    "Продажи",
    "Разработка",
    "CRM",
    "Реклама",
    "Дизайн",
    "Аналитика",
    "Интегратор",
    "IT",
    "Образование",
    "Маркетплейсы",
    "Другое",
)

PROFILE_STATUSES: tuple[str, ...] = tuple(status.value for status in ProfileStatus)
PROFILE_VIEW_ACTIONS: tuple[str, ...] = tuple(
    action.value for action in ProfileViewAction
)
RANDOM_COFFEE_ROUND_STATUSES: tuple[str, ...] = tuple(
    status.value for status in RandomCoffeeRoundStatus
)
RANDOM_COFFEE_ANSWERS: tuple[str, ...] = tuple(
    answer.value for answer in RandomCoffeeAnswerValue
)
