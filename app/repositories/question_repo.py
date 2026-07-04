from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.questions import QUESTIONS
from app.db.models import QuestionRecord
from app.models.enums import Difficulty, JlptLevel, QuestionType
from app.schemas.question import LocalizedQuestionContent, Question


def _content_to_dict(content: LocalizedQuestionContent) -> dict:
    return content.model_dump()


def _record_to_question(record: QuestionRecord) -> Question:
    return Question(
        id=record.id,
        jlpt_level=JlptLevel(record.jlpt_level),
        difficulty=Difficulty(record.difficulty),
        question_type=QuestionType(record.question_type),
        prompt=record.prompt,
        content_en=LocalizedQuestionContent(**record.content_en),
        content_ja=LocalizedQuestionContent(**record.content_ja),
    )


class QuestionRepository:
    def seed_initial_questions(self, db: Session) -> None:
        existing_records = db.scalars(select(QuestionRecord)).all()
        existing_by_id = {record.id: record for record in existing_records}

        for question in QUESTIONS:
            record = existing_by_id.get(question.id)
            if record is None:
                db.add(
                    QuestionRecord(
                        id=question.id,
                        jlpt_level=question.jlpt_level.value,
                        difficulty=question.difficulty.value,
                        question_type=question.question_type.value,
                        prompt=question.prompt,
                        content_en=_content_to_dict(question.content_en),
                        content_ja=_content_to_dict(question.content_ja),
                    )
                )
            else:
                record.jlpt_level = question.jlpt_level.value
                record.difficulty = question.difficulty.value
                record.question_type = question.question_type.value
                record.prompt = question.prompt
                record.content_en = _content_to_dict(question.content_en)
                record.content_ja = _content_to_dict(question.content_ja)
        db.commit()

    def upsert_many(self, db: Session, questions: list[Question]) -> None:
        if not questions:
            return

        existing_records = db.scalars(
            select(QuestionRecord).where(
                QuestionRecord.id.in_([question.id for question in questions])
            )
        ).all()
        existing_by_id = {record.id: record for record in existing_records}

        for question in questions:
            record = existing_by_id.get(question.id)
            if record is None:
                db.add(
                    QuestionRecord(
                        id=question.id,
                        jlpt_level=question.jlpt_level.value,
                        difficulty=question.difficulty.value,
                        question_type=question.question_type.value,
                        prompt=question.prompt,
                        content_en=_content_to_dict(question.content_en),
                        content_ja=_content_to_dict(question.content_ja),
                    )
                )
                continue

            record.jlpt_level = question.jlpt_level.value
            record.difficulty = question.difficulty.value
            record.question_type = question.question_type.value
            record.prompt = question.prompt
            record.content_en = _content_to_dict(question.content_en)
            record.content_ja = _content_to_dict(question.content_ja)

        db.commit()

    def list(
        self,
        db: Session,
        jlpt_level: JlptLevel | None = None,
        difficulty: Difficulty | None = None,
        limit: int | None = None,
    ) -> list[Question]:
        stmt = select(QuestionRecord)
        if jlpt_level is not None:
            stmt = stmt.where(QuestionRecord.jlpt_level == jlpt_level.value)
        if difficulty is not None:
            stmt = stmt.where(QuestionRecord.difficulty == difficulty.value)
        if limit is not None:
            stmt = stmt.limit(limit)

        return [_record_to_question(record) for record in db.scalars(stmt).all()]

    def get(self, db: Session, question_id: int) -> Question | None:
        record = db.get(QuestionRecord, question_id)
        if record is None:
            return None
        return _record_to_question(record)
