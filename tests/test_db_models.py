from sqlalchemy import Index, UniqueConstraint

from ds_chat_bot.db.base import Base
from ds_chat_bot.db.models import (
    Profile,
    ProfileView,
    RandomCoffeeAnswer,
    RandomCoffeeRound,
    User,
)


def test_metadata_contains_expected_mvp_tables() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "profiles",
        "profile_views",
        "random_coffee_rounds",
        "random_coffee_answers",
        "random_coffee_pairs",
    }


def test_user_columns_and_indexes_are_defined() -> None:
    users = User.__table__

    assert users.c.telegram_id.type.python_type is int
    assert users.c.telegram_id.nullable is False
    assert users.c.telegram_id.index is True
    assert users.c.telegram_id.unique is True
    assert users.c.is_admin.nullable is False
    assert users.c.is_blocked.nullable is False
    assert users.c.created_at.type.timezone is True
    assert users.c.updated_at.type.timezone is True


def test_profile_columns_constraints_and_indexes_are_defined() -> None:
    profiles = Profile.__table__

    assert profiles.c.user_id.nullable is False
    assert profiles.c.user_id.index is True
    assert profiles.c.user_id.unique is True
    assert profiles.c.category.index is True
    assert profiles.c.status.index is True
    assert profiles.c.allow_contact_reveal.nullable is False
    assert profiles.c.created_at.type.timezone is True
    assert profiles.c.updated_at.type.timezone is True
    assert {constraint.name for constraint in profiles.constraints} >= {
        "ck_profiles_status",
        "ck_profiles_category",
    }


def test_profile_view_terminal_action_unique_index_is_defined() -> None:
    profile_views = ProfileView.__table__
    terminal_indexes = [
        index
        for index in profile_views.indexes
        if index.name == "uq_profile_views_terminal_action"
    ]

    assert len(terminal_indexes) == 1
    terminal_index = terminal_indexes[0]
    assert isinstance(terminal_index, Index)
    assert terminal_index.unique is True
    assert [column.name for column in terminal_index.columns] == [
        "viewer_user_id",
        "profile_id",
        "action",
    ]
    assert (
        str(terminal_index.dialect_options["postgresql"]["where"])
        == "action IN ('liked', 'skipped')"
    )


def test_random_coffee_round_and_answer_constraints_are_defined() -> None:
    rounds = RandomCoffeeRound.__table__
    answers = RandomCoffeeAnswer.__table__

    assert rounds.c.week_start.nullable is False
    assert rounds.c.week_start.index is True
    assert rounds.c.week_start.unique is True
    assert rounds.c.status.index is True
    assert "ck_random_coffee_rounds_status" in {
        constraint.name for constraint in rounds.constraints
    }

    unique_constraints = [
        constraint
        for constraint in answers.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    assert any(
        constraint.name == "uq_random_coffee_answers_round_user"
        for constraint in unique_constraints
    )
    assert answers.c.answer.index is True
    assert answers.c.answered_at.type.timezone is True
