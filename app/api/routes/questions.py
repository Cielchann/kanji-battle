from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_question_repository
from app.db.session import get_db
from app.models.enums import Difficulty, DisplayLanguage, JlptLevel, QuestionType
from app.repositories.question_repo import QuestionRepository
from app.schemas.question import PublicQuestion, to_public_question

router = APIRouter()


@router.get("", response_model=list[PublicQuestion])
def list_questions(
    jlpt_level: JlptLevel | None = None,
    difficulty: Difficulty | None = None,
    language: DisplayLanguage = DisplayLanguage.EN,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    repository: QuestionRepository = Depends(get_question_repository),
) -> list[PublicQuestion]:
    query_limit = None if language == DisplayLanguage.JA else limit
    questions = repository.list(db, jlpt_level=jlpt_level, difficulty=difficulty, limit=query_limit)
    if language == DisplayLanguage.JA:
        questions = [
            question
            for question in questions
            if question.question_type == QuestionType.KANJI_READING
        ][:limit]
    return [to_public_question(question, language) for question in questions]
