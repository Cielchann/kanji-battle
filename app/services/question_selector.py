import random

from app.models.enums import Difficulty, DisplayLanguage, JlptLevel, QuestionType
from app.schemas.question import Question


QUESTION_LEVEL_WEIGHTS: dict[Difficulty, dict[JlptLevel, int]] = {
    Difficulty.EASY: {
        JlptLevel.N5: 70,
        JlptLevel.N4: 30,
    },
    Difficulty.MEDIUM: {
        JlptLevel.N5: 20,
        JlptLevel.N4: 50,
        JlptLevel.N3: 30,
    },
    Difficulty.HARD: {
        JlptLevel.N4: 20,
        JlptLevel.N3: 50,
        JlptLevel.N2: 30,
    },
    Difficulty.EXTREME: {
        JlptLevel.N3: 15,
        JlptLevel.N2: 55,
        JlptLevel.N1: 30,
    },
    Difficulty.HELL: {
        JlptLevel.N2: 25,
        JlptLevel.N1: 75,
    },
}


class QuestionSelector:
    def __init__(self, questions: list[Question]) -> None:
        self._questions = questions

    def by_level(self, jlpt_level: JlptLevel | None) -> list[Question]:
        return [
            question
            for question in self._questions
            if jlpt_level is None or question.jlpt_level == jlpt_level
        ]

    def by_language(self, questions: list[Question], language: DisplayLanguage) -> list[Question]:
        if language == DisplayLanguage.JA:
            return [
                question
                for question in questions
                if question.question_type == QuestionType.KANJI_READING
            ]
        return questions

    def next_question(
        self,
        jlpt_level: JlptLevel | None,
        difficulty: Difficulty,
        used_question_ids: set[int],
        language: DisplayLanguage = DisplayLanguage.EN,
    ) -> Question:
        level_questions = self.by_language(self.by_level(jlpt_level), language)
        candidates = [question for question in level_questions if question.id not in used_question_ids]
        if not candidates:
            candidates = level_questions
        if not candidates:
            level_label = jlpt_level if jlpt_level is not None else "N5-N1"
            msg = f"No questions available for JLPT level {level_label} and language {language}."
            raise ValueError(msg)

        if jlpt_level is not None:
            return random.choice(candidates)

        weights = QUESTION_LEVEL_WEIGHTS[difficulty]
        available_levels = {
            question.jlpt_level
            for question in candidates
            if question.jlpt_level in weights
        }
        if not available_levels:
            return random.choice(candidates)

        weighted_levels = list(available_levels)
        level_weights = [weights[level] for level in weighted_levels]
        selected_level = random.choices(weighted_levels, weights=level_weights, k=1)[0]
        level_candidates = [
            question for question in candidates if question.jlpt_level == selected_level
        ]
        return random.choice(level_candidates)
