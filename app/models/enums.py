from enum import StrEnum


class JlptLevel(StrEnum):
    N5 = "N5"
    N4 = "N4"
    N3 = "N3"
    N2 = "N2"
    N1 = "N1"


class QuestionType(StrEnum):
    KANJI_READING = "kanji_reading"
    VOCAB_MEANING = "vocab_meaning"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTREME = "extreme"
    HELL = "hell"


class DisplayLanguage(StrEnum):
    EN = "en"
    JA = "ja"


class BattleStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"
