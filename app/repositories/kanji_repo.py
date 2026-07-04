from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import KanjiEntryRecord
from app.schemas.kanji import KanjiEntry


def _record_to_schema(record: KanjiEntryRecord) -> KanjiEntry:
    return KanjiEntry(
        character=record.character,
        meanings=record.meanings,
        kun_readings=record.kun_readings,
        on_readings=record.on_readings,
        name_readings=record.name_readings,
        stroke_count=record.stroke_count,
        grade=record.grade,
        jlpt=record.jlpt,
        unicode=record.unicode,
        power=record.power,
        source=record.source,
    )


class KanjiRepository:
    def get(self, db: Session, character: str) -> KanjiEntry | None:
        record = db.get(KanjiEntryRecord, character)
        if record is None:
            return None
        return _record_to_schema(record)

    def list(self, db: Session, limit: int = 500) -> list[KanjiEntry]:
        records = db.scalars(
            select(KanjiEntryRecord)
            .order_by(KanjiEntryRecord.power, KanjiEntryRecord.character)
            .limit(limit)
        ).all()
        return [_record_to_schema(record) for record in records]

    def save(self, db: Session, entry: KanjiEntry) -> KanjiEntry:
        record = db.get(KanjiEntryRecord, entry.character)
        if record is None:
            record = KanjiEntryRecord(character=entry.character)
            db.add(record)

        record.meanings = entry.meanings
        record.kun_readings = entry.kun_readings
        record.on_readings = entry.on_readings
        record.name_readings = entry.name_readings
        record.stroke_count = entry.stroke_count
        record.grade = entry.grade
        record.jlpt = entry.jlpt
        record.unicode = entry.unicode
        record.power = entry.power
        record.source = entry.source
        record.cached_at = datetime.now(timezone.utc)
        db.commit()
        return entry
