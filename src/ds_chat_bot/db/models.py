"""SQLAlchemy ORM models for the DS_chat_bot MVP database."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ds_chat_bot.db.base import Base, utc_now
from ds_chat_bot.db.constants import (
    CATEGORIES,
    PROFILE_STATUSES,
    PROFILE_VIEW_ACTIONS,
    RANDOM_COFFEE_ANSWERS,
    RANDOM_COFFEE_ROUND_STATUSES,
    ProfileStatus,
    RandomCoffeeRoundStatus,
)


def _quoted_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


class User(Base):
    """Telegram user known by the bot."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Profile(Base):
    """Participant questionnaire used for partner discovery."""

    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_quoted_values(PROFILE_STATUSES)})", name="ck_profiles_status"
        ),
        CheckConstraint(
            f"category IN ({_quoted_values(CATEGORIES)})", name="ck_profiles_category"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    company_site: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    function_description: Mapped[str] = mapped_column(Text, nullable=False)
    tasks_description: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hobbies: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram_username: Mapped[str] = mapped_column(String(255), nullable=False)
    allow_contact_reveal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ProfileStatus.DRAFT.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    user: Mapped[User] = relationship(back_populates="profile")
    views: Mapped[list["ProfileView"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class ProfileView(Base):
    """A profile discovery event recorded for a viewer."""

    __tablename__ = "profile_views"
    __table_args__ = (
        CheckConstraint(
            f"action IN ({_quoted_values(PROFILE_VIEW_ACTIONS)})",
            name="ck_profile_views_action",
        ),
        CheckConstraint(
            f"category IS NULL OR category IN ({_quoted_values(CATEGORIES)})",
            name="ck_profile_views_category",
        ),
        Index(
            "uq_profile_views_terminal_action",
            "viewer_user_id",
            "profile_id",
            "action",
            unique=True,
            postgresql_where=text("action IN ('liked', 'skipped')"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    viewer_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    viewer: Mapped[User] = relationship(foreign_keys=[viewer_user_id])
    profile: Mapped[Profile] = relationship(back_populates="views")


class RandomCoffeeRound(Base):
    """Weekly Random Coffee round."""

    __tablename__ = "random_coffee_rounds"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_quoted_values(RANDOM_COFFEE_ROUND_STATUSES)})",
            name="ck_random_coffee_rounds_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start: Mapped[date] = mapped_column(
        Date, nullable=False, unique=True, index=True
    )
    poll_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    pairs_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RandomCoffeeRoundStatus.DRAFT.value,
        index=True,
    )

    answers: Mapped[list["RandomCoffeeAnswer"]] = relationship(
        back_populates="round", cascade="all, delete-orphan"
    )
    pairs: Mapped[list["RandomCoffeePair"]] = relationship(
        back_populates="round", cascade="all, delete-orphan"
    )


class RandomCoffeeAnswer(Base):
    """User response to a Random Coffee poll."""

    __tablename__ = "random_coffee_answers"
    __table_args__ = (
        UniqueConstraint(
            "round_id", "user_id", name="uq_random_coffee_answers_round_user"
        ),
        CheckConstraint(
            f"answer IN ({_quoted_values(RANDOM_COFFEE_ANSWERS)})",
            name="ck_random_coffee_answers_answer",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("random_coffee_rounds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answer: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    round: Mapped[RandomCoffeeRound] = relationship(back_populates="answers")
    user: Mapped[User] = relationship()


class RandomCoffeePair(Base):
    """Generated pair or trio for a Random Coffee round."""

    __tablename__ = "random_coffee_pairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("random_coffee_rounds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_1_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_2_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_3_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    round: Mapped[RandomCoffeeRound] = relationship(back_populates="pairs")
    user_1: Mapped[User] = relationship(foreign_keys=[user_1_id])
    user_2: Mapped[User] = relationship(foreign_keys=[user_2_id])
    user_3: Mapped[User | None] = relationship(foreign_keys=[user_3_id])
