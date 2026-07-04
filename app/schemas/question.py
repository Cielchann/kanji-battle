import random

from pydantic import BaseModel, Field

from app.models.enums import Difficulty, DisplayLanguage, JlptLevel, QuestionType


QUESTION_POWER_BY_JLPT_LEVEL: dict[JlptLevel, int] = {
    JlptLevel.N5: 1,
    JlptLevel.N4: 2,
    JlptLevel.N3: 3,
    JlptLevel.N2: 4,
    JlptLevel.N1: 5,
}


class LocalizedQuestionContent(BaseModel):
    question_text: str
    choices: list[str] = Field(min_length=2)
    correct_answer: str
    explanation: str | None = None


class Question(BaseModel):
    id: int
    jlpt_level: JlptLevel
    difficulty: Difficulty
    question_type: QuestionType
    prompt: str
    content_en: LocalizedQuestionContent
    content_ja: LocalizedQuestionContent


class PublicQuestion(BaseModel):
    id: int
    jlpt_level: JlptLevel
    difficulty: Difficulty
    question_type: QuestionType
    language: DisplayLanguage
    question_text: str
    prompt: str
    choices: list[str]
    power: int = Field(ge=1, le=5)


def get_localized_content(
    question: Question,
    language: DisplayLanguage,
) -> LocalizedQuestionContent:
    if language == DisplayLanguage.JA:
        return question.content_ja
    return question.content_en


def to_public_question(
    question: Question,
    language: DisplayLanguage = DisplayLanguage.EN,
) -> PublicQuestion:
    content = get_localized_content(question, language)
    choices = random.sample(content.choices, k=len(content.choices))
    return PublicQuestion(
        id=question.id,
        jlpt_level=question.jlpt_level,
        difficulty=question.difficulty,
        question_type=question.question_type,
        language=language,
        question_text=content.question_text,
        prompt=question.prompt,
        choices=choices,
        power=QUESTION_POWER_BY_JLPT_LEVEL[question.jlpt_level],
    )
