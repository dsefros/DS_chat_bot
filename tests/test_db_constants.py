from ds_chat_bot.db.constants import (
    CATEGORIES,
    PROFILE_STATUSES,
    PROFILE_VIEW_ACTIONS,
    RANDOM_COFFEE_ANSWERS,
    RANDOM_COFFEE_ROUND_STATUSES,
)


def test_mvp_categories_match_required_list() -> None:
    assert CATEGORIES == (
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


def test_status_and_action_constants_match_required_values() -> None:
    assert PROFILE_STATUSES == (
        "draft",
        "pending_review",
        "approved",
        "rejected",
        "hidden",
    )
    assert PROFILE_VIEW_ACTIONS == ("viewed", "liked", "skipped", "contact_revealed")
    assert RANDOM_COFFEE_ROUND_STATUSES == ("draft", "polling", "paired", "cancelled")
    assert RANDOM_COFFEE_ANSWERS == ("yes", "no")
