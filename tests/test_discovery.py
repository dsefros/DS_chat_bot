from ds_chat_bot.callbacks import (
    DISCOVERY_CATEGORIES_CALLBACK,
    DISCOVERY_CATEGORY_PREFIX,
    DISCOVERY_LIKE_PREFIX,
    DISCOVERY_MENU_CALLBACK,
    DISCOVERY_SKIP_PREFIX,
)
from ds_chat_bot.db.constants import ProfileStatus, ProfileViewAction
from ds_chat_bot.db.models import Profile
from ds_chat_bot.discovery import (
    discovery_access_for_profile,
    format_discovery_profile_card,
    is_profile_approved_for_discovery,
    no_more_profiles_message,
    parse_discovery_category_callback,
    parse_discovery_profile_callback,
)


def make_profile(**overrides) -> Profile:
    values = {
        "user_id": 2,
        "name": "Анна",
        "company": "Acme",
        "category": "Маркетинг",
        "position": "CMO",
        "function_description": "Маркетинговая стратегия",
        "tasks_description": "Помогает расти продажам",
        "city": "Москва",
        "hobbies": "Бег",
        "telegram_username": "@anna_secret",
        "allow_contact_reveal": True,
        "status": ProfileStatus.APPROVED.value,
    }
    values.update(overrides)
    return Profile(**values)


def test_discovery_card_format_hides_telegram_and_internal_fields() -> None:
    profile = make_profile(id=55)

    card = format_discovery_profile_card(profile)

    assert "Анкета участника" in card
    assert "@anna_secret" not in card
    assert "Telegram" not in card
    assert "Profile ID" not in card
    assert "55" not in card
    assert ProfileStatus.APPROVED.value not in card
    assert "allow_contact_reveal" not in card


def test_discovery_access_requires_approved_profile() -> None:
    assert discovery_access_for_profile(None).reason == "missing_profile"

    pending = discovery_access_for_profile(make_profile(status=ProfileStatus.PENDING_REVIEW.value))
    rejected = discovery_access_for_profile(make_profile(status=ProfileStatus.REJECTED.value))
    approved = discovery_access_for_profile(make_profile(status=ProfileStatus.APPROVED.value))
    hidden = discovery_access_for_profile(make_profile(status=ProfileStatus.HIDDEN.value))

    assert pending.allowed is False
    assert pending.reason == "pending_review"
    assert rejected.allowed is False
    assert rejected.reason == "rejected"
    assert approved.allowed is True
    assert approved.reason == "approved"
    assert hidden.allowed is False
    assert hidden.reason == "not_approved"


def test_profile_status_eligibility_helper() -> None:
    assert is_profile_approved_for_discovery(make_profile(status=ProfileStatus.APPROVED.value)) is True
    assert is_profile_approved_for_discovery(make_profile(status=ProfileStatus.DRAFT.value)) is False
    assert is_profile_approved_for_discovery(None) is False


def test_category_callback_parser_accepts_only_discovery_categories() -> None:
    assert parse_discovery_category_callback(f"{DISCOVERY_CATEGORY_PREFIX}Маркетинг") == "Маркетинг"
    assert parse_discovery_category_callback("profile:category:Маркетинг") is None
    assert parse_discovery_category_callback(f"{DISCOVERY_CATEGORY_PREFIX}Не категория") is None
    assert parse_discovery_category_callback(None) is None


def test_profile_callback_parser_accepts_positive_integer_ids() -> None:
    assert parse_discovery_profile_callback(f"{DISCOVERY_LIKE_PREFIX}123", DISCOVERY_LIKE_PREFIX) == 123
    assert parse_discovery_profile_callback(f"{DISCOVERY_LIKE_PREFIX}0", DISCOVERY_LIKE_PREFIX) is None
    assert parse_discovery_profile_callback(f"{DISCOVERY_LIKE_PREFIX}abc", DISCOVERY_LIKE_PREFIX) is None
    assert parse_discovery_profile_callback("discovery:skip:123", DISCOVERY_LIKE_PREFIX) is None


def test_profile_view_action_constants_match_discovery_actions() -> None:
    assert ProfileViewAction.VIEWED.value == "viewed"
    assert ProfileViewAction.LIKED.value == "liked"
    assert ProfileViewAction.SKIPPED.value == "skipped"
    assert ProfileViewAction.CONTACT_REVEALED.value == "contact_revealed"


def test_no_more_profiles_message_helper() -> None:
    assert no_more_profiles_message() == "Упс, анкеты закончились!\nВыбери другую категорию или загляни попозже."


def test_discovery_callback_constants_are_stable() -> None:
    assert DISCOVERY_CATEGORY_PREFIX == "discovery:category:"
    assert DISCOVERY_LIKE_PREFIX == "discovery:like:"
    assert DISCOVERY_SKIP_PREFIX == "discovery:skip:"
    assert DISCOVERY_CATEGORIES_CALLBACK == "discovery:categories"
    assert DISCOVERY_MENU_CALLBACK == "discovery:menu"
