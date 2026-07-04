from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def current_week_start() -> date:
    today = datetime.now(timezone.utc).date()
    return today.fromordinal(today.toordinal() - today.weekday())


class QuestionRecord(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jlpt_level: Mapped[str] = mapped_column(String(2), index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    question_type: Mapped[str] = mapped_column(String(40))
    prompt: Mapped[str] = mapped_column(String(255))
    content_en: Mapped[dict] = mapped_column(JSON)
    content_ja: Mapped[dict] = mapped_column(JSON)


class KanjiEntryRecord(Base):
    __tablename__ = "kanji_entries"

    character: Mapped[str] = mapped_column(String(8), primary_key=True)
    meanings: Mapped[list[str]] = mapped_column(JSON)
    kun_readings: Mapped[list[str]] = mapped_column(JSON)
    on_readings: Mapped[list[str]] = mapped_column(JSON)
    name_readings: Mapped[list[str]] = mapped_column(JSON)
    stroke_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jlpt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unicode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    power: Mapped[int] = mapped_column(Integer, default=3, index=True)
    source: Mapped[str] = mapped_column(String(80), default="kanjiapi.dev")
    cached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class BattleSessionRecord(Base):
    __tablename__ = "battle_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    player_name: Mapped[str] = mapped_column(String(80), default="Guest Player")
    jlpt_level: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    language: Mapped[str] = mapped_column(String(2))
    player_hp: Mapped[int] = mapped_column(Integer)
    monster_name: Mapped[str] = mapped_column(String(120))
    monster_max_hp: Mapped[int] = mapped_column(Integer)
    monster_hp: Mapped[int] = mapped_column(Integer)
    weapon_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    weapon_attack_bonus: Mapped[int] = mapped_column(Integer, default=0)
    combo: Mapped[int] = mapped_column(Integer)
    max_combo: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    gold_earned: Mapped[int] = mapped_column(Integer, default=0)
    turn: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), index=True)
    current_question_id: Mapped[int | None] = mapped_column(
        ForeignKey("questions.id"),
        nullable=True,
    )
    used_question_ids: Mapped[list[int]] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BattleTurnRecord(Base):
    __tablename__ = "battle_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    battle_id: Mapped[str] = mapped_column(ForeignKey("battle_sessions.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    user_answer: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    damage_dealt: Mapped[int] = mapped_column(Integer)
    damage_taken: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ScoreRecord(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    battle_id: Mapped[str] = mapped_column(ForeignKey("battle_sessions.id"), unique=True)
    player_name: Mapped[str] = mapped_column(String(80), default="Demo Player")
    jlpt_level: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    score: Mapped[int] = mapped_column(Integer)
    max_combo: Mapped[int] = mapped_column(Integer)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    gold_earned: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30))
    week_start: Mapped[date] = mapped_column(Date, default=current_week_start, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PlayerProfileRecord(Base):
    __tablename__ = "player_profiles"

    player_name: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    hero_role: Mapped[str] = mapped_column(String(40), default="Hero")
    xp: Mapped[int] = mapped_column(Integer, default=0)
    gold: Mapped[int] = mapped_column(Integer, default=0)
    total_clears: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class DifficultyProgressRecord(Base):
    __tablename__ = "difficulty_progress"
    __table_args__ = (
        UniqueConstraint("player_name", "difficulty", name="uq_player_difficulty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_name: Mapped[str] = mapped_column(String(80), index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    clears: Mapped[int] = mapped_column(Integer, default=0)
    perfect_clears: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class WeaponRecord(Base):
    __tablename__ = "weapons"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    required_role: Mapped[str] = mapped_column(String(40), default="Hero")
    price: Mapped[int] = mapped_column(Integer)
    attack_bonus: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")


class PlayerWeaponRecord(Base):
    __tablename__ = "player_weapons"
    __table_args__ = (
        UniqueConstraint("player_name", "weapon_id", name="uq_player_weapon"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_name: Mapped[str] = mapped_column(String(80), index=True)
    weapon_id: Mapped[str] = mapped_column(ForeignKey("weapons.id"), index=True)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
