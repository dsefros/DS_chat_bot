"""create mvp database tables.

Revision ID: 20260528_0001
Revises:
Create Date: 2026-05-28 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260528_0001"
down_revision = None
branch_labels = None
depends_on = None

PROFILE_STATUSES = ("draft", "pending_review", "approved", "rejected", "hidden")
PROFILE_VIEW_ACTIONS = ("viewed", "liked", "skipped", "contact_revealed")
RANDOM_COFFEE_ROUND_STATUSES = ("draft", "polling", "paired", "cancelled")
RANDOM_COFFEE_ANSWERS = ("yes", "no")
CATEGORIES = (
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


def _quoted_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("company_site", sa.String(length=512), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("position", sa.String(length=255), nullable=False),
        sa.Column("function_description", sa.Text(), nullable=False),
        sa.Column("tasks_description", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("hobbies", sa.Text(), nullable=True),
        sa.Column("telegram_username", sa.String(length=255), nullable=False),
        sa.Column("allow_contact_reveal", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"category IN ({_quoted_values(CATEGORIES)})", name="ck_profiles_category"
        ),
        sa.CheckConstraint(
            f"status IN ({_quoted_values(PROFILE_STATUSES)})", name="ck_profiles_status"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_profiles_category"), "profiles", ["category"], unique=False
    )
    op.create_index(op.f("ix_profiles_status"), "profiles", ["status"], unique=False)
    op.create_index(op.f("ix_profiles_user_id"), "profiles", ["user_id"], unique=True)

    op.create_table(
        "random_coffee_rounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("poll_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pairs_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            f"status IN ({_quoted_values(RANDOM_COFFEE_ROUND_STATUSES)})",
            name="ck_random_coffee_rounds_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_random_coffee_rounds_status"),
        "random_coffee_rounds",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_random_coffee_rounds_week_start"),
        "random_coffee_rounds",
        ["week_start"],
        unique=True,
    )

    op.create_table(
        "profile_views",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("viewer_user_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"action IN ({_quoted_values(PROFILE_VIEW_ACTIONS)})",
            name="ck_profile_views_action",
        ),
        sa.CheckConstraint(
            f"category IS NULL OR category IN ({_quoted_values(CATEGORIES)})",
            name="ck_profile_views_category",
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_profile_views_action"), "profile_views", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_profile_views_profile_id"),
        "profile_views",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_profile_views_viewer_user_id"),
        "profile_views",
        ["viewer_user_id"],
        unique=False,
    )
    op.create_index(
        "uq_profile_views_terminal_action",
        "profile_views",
        ["viewer_user_id", "profile_id", "action"],
        unique=True,
        postgresql_where=sa.text("action IN ('liked', 'skipped')"),
    )

    op.create_table(
        "random_coffee_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("answer", sa.String(length=8), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"answer IN ({_quoted_values(RANDOM_COFFEE_ANSWERS)})",
            name="ck_random_coffee_answers_answer",
        ),
        sa.ForeignKeyConstraint(
            ["round_id"], ["random_coffee_rounds.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "round_id", "user_id", name="uq_random_coffee_answers_round_user"
        ),
    )
    op.create_index(
        op.f("ix_random_coffee_answers_answer"),
        "random_coffee_answers",
        ["answer"],
        unique=False,
    )
    op.create_index(
        op.f("ix_random_coffee_answers_round_id"),
        "random_coffee_answers",
        ["round_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_random_coffee_answers_user_id"),
        "random_coffee_answers",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "random_coffee_pairs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("user_1_id", sa.Integer(), nullable=False),
        sa.Column("user_2_id", sa.Integer(), nullable=False),
        sa.Column("user_3_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["round_id"], ["random_coffee_rounds.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_1_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_2_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_3_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_random_coffee_pairs_round_id"),
        "random_coffee_pairs",
        ["round_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_random_coffee_pairs_round_id"), table_name="random_coffee_pairs"
    )
    op.drop_table("random_coffee_pairs")
    op.drop_index(
        op.f("ix_random_coffee_answers_user_id"), table_name="random_coffee_answers"
    )
    op.drop_index(
        op.f("ix_random_coffee_answers_round_id"), table_name="random_coffee_answers"
    )
    op.drop_index(
        op.f("ix_random_coffee_answers_answer"), table_name="random_coffee_answers"
    )
    op.drop_table("random_coffee_answers")
    op.drop_index(
        "uq_profile_views_terminal_action",
        table_name="profile_views",
        postgresql_where=sa.text("action IN ('liked', 'skipped')"),
    )
    op.drop_index(op.f("ix_profile_views_viewer_user_id"), table_name="profile_views")
    op.drop_index(op.f("ix_profile_views_profile_id"), table_name="profile_views")
    op.drop_index(op.f("ix_profile_views_action"), table_name="profile_views")
    op.drop_table("profile_views")
    op.drop_index(
        op.f("ix_random_coffee_rounds_week_start"), table_name="random_coffee_rounds"
    )
    op.drop_index(
        op.f("ix_random_coffee_rounds_status"), table_name="random_coffee_rounds"
    )
    op.drop_table("random_coffee_rounds")
    op.drop_index(op.f("ix_profiles_user_id"), table_name="profiles")
    op.drop_index(op.f("ix_profiles_status"), table_name="profiles")
    op.drop_index(op.f("ix_profiles_category"), table_name="profiles")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
