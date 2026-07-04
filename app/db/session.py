from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.engine import create_database_engine

settings = get_settings()
database_url = settings.database_url

engine = create_database_engine(database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()


def ensure_sqlite_schema() -> None:
    if not database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        battle_columns = connection.execute(text("PRAGMA table_info(battle_sessions)")).all()
        battle_column_names = {column[1] for column in battle_columns}
        if battle_columns and "player_name" not in battle_column_names:
            connection.execute(
                text(
                    "ALTER TABLE battle_sessions "
                    "ADD COLUMN player_name VARCHAR(80) DEFAULT 'Guest Player'"
                )
            )
        if battle_columns and "xp_earned" not in battle_column_names:
            connection.execute(
                text("ALTER TABLE battle_sessions ADD COLUMN xp_earned INTEGER DEFAULT 0")
            )
        if battle_columns and "gold_earned" not in battle_column_names:
            connection.execute(
                text("ALTER TABLE battle_sessions ADD COLUMN gold_earned INTEGER DEFAULT 0")
            )
        if battle_columns and "weapon_name" not in battle_column_names:
            connection.execute(
                text("ALTER TABLE battle_sessions ADD COLUMN weapon_name VARCHAR(80)")
            )
        if battle_columns and "weapon_attack_bonus" not in battle_column_names:
            connection.execute(
                text("ALTER TABLE battle_sessions ADD COLUMN weapon_attack_bonus INTEGER DEFAULT 0")
            )

        score_columns = connection.execute(text("PRAGMA table_info(scores)")).all()
        score_column_names = {column[1] for column in score_columns}
        if score_columns and "xp_earned" not in score_column_names:
            connection.execute(text("ALTER TABLE scores ADD COLUMN xp_earned INTEGER DEFAULT 0"))
        if score_columns and "gold_earned" not in score_column_names:
            connection.execute(text("ALTER TABLE scores ADD COLUMN gold_earned INTEGER DEFAULT 0"))
        if score_columns and "week_start" not in score_column_names:
            connection.execute(text("ALTER TABLE scores ADD COLUMN week_start DATE"))

        profile_columns = connection.execute(text("PRAGMA table_info(player_profiles)")).all()
        profile_column_names = {column[1] for column in profile_columns}
        if profile_columns and "owner_token" not in profile_column_names:
            connection.execute(
                text("ALTER TABLE player_profiles ADD COLUMN owner_token VARCHAR(128)")
            )


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
