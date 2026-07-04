from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.engine import create_database_engine
from app.db.models import KanjiEntryRecord, QuestionRecord, WeaponRecord


ROOT_DIR = Path(__file__).resolve().parent.parent
SQLITE_URL = f"sqlite:///{(ROOT_DIR / 'jlpt_battle.db').as_posix()}"


def main() -> None:
    source_engine = create_engine(SQLITE_URL)
    target_engine = create_database_engine(get_settings().database_url)

    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)

    kanji_count = 0
    question_count = 0
    weapon_count = 0

    with SourceSession() as source, TargetSession() as target:
        for source_record in source.scalars(select(KanjiEntryRecord)).all():
            target.merge(
                KanjiEntryRecord(
                    character=source_record.character,
                    meanings=source_record.meanings,
                    kun_readings=source_record.kun_readings,
                    on_readings=source_record.on_readings,
                    name_readings=source_record.name_readings,
                    stroke_count=source_record.stroke_count,
                    grade=source_record.grade,
                    jlpt=source_record.jlpt,
                    unicode=source_record.unicode,
                    power=source_record.power,
                    source=source_record.source,
                    cached_at=source_record.cached_at,
                )
            )
            kanji_count += 1

        for source_record in source.scalars(select(QuestionRecord)).all():
            target.merge(
                QuestionRecord(
                    id=source_record.id,
                    jlpt_level=source_record.jlpt_level,
                    difficulty=source_record.difficulty,
                    question_type=source_record.question_type,
                    prompt=source_record.prompt,
                    content_en=source_record.content_en,
                    content_ja=source_record.content_ja,
                )
            )
            question_count += 1

        for source_record in source.scalars(select(WeaponRecord)).all():
            target.merge(
                WeaponRecord(
                    id=source_record.id,
                    name=source_record.name,
                    required_role=source_record.required_role,
                    price=source_record.price,
                    attack_bonus=source_record.attack_bonus,
                    description=source_record.description,
                )
            )
            weapon_count += 1

        target.commit()

    print(f"kanji_synced={kanji_count}")
    print(f"questions_synced={question_count}")
    print(f"weapons_synced={weapon_count}")


if __name__ == "__main__":
    main()
