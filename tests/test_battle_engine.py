from app.data.questions import QUESTIONS
from app.models.enums import BattleStatus, Difficulty, DisplayLanguage, JlptLevel
from app.services.battle_engine import BattleEngine
from app.services.battle_balance import PLAYER_HP_BY_DIFFICULTY
from app.services.question_selector import QuestionSelector
from app.schemas.question import get_localized_content


def test_correct_answer_deals_damage_and_increases_combo() -> None:
    engine = BattleEngine(QuestionSelector(QUESTIONS))
    session = engine.start("Afras", JlptLevel.N5, Difficulty.EASY, DisplayLanguage.EN)
    question = session.current_question

    assert session.player_name == "Afras"
    assert question is not None
    content = get_localized_content(question, session.language)

    is_correct, damage_dealt, damage_taken, _ = engine.answer(
        session,
        question.id,
        content.correct_answer,
    )

    assert is_correct is True
    assert damage_dealt > 0
    assert damage_taken == 0
    assert session.combo == 1
    assert session.score > 0


def test_wrong_answer_damages_player_and_resets_combo() -> None:
    engine = BattleEngine(QuestionSelector(QUESTIONS))
    session = engine.start("Afras", JlptLevel.N5, Difficulty.EASY, DisplayLanguage.EN)
    question = session.current_question

    assert question is not None
    content = get_localized_content(question, session.language)

    engine.answer(session, question.id, content.correct_answer)
    second_question = session.current_question

    assert second_question is not None

    is_correct, damage_dealt, damage_taken, _ = engine.answer(
        session,
        second_question.id,
        "wrong answer",
    )

    assert is_correct is False
    assert damage_dealt == 0
    assert damage_taken > 0
    assert session.combo == 0
    assert session.player_hp < PLAYER_HP_BY_DIFFICULTY[Difficulty.EASY]


def test_battle_can_be_won() -> None:
    engine = BattleEngine(QuestionSelector(QUESTIONS))
    session = engine.start("Afras", JlptLevel.N5, Difficulty.EASY, DisplayLanguage.EN)

    answer_count = 0
    while session.status == BattleStatus.IN_PROGRESS:
        question = session.current_question
        assert question is not None
        content = get_localized_content(question, session.language)
        engine.answer(session, question.id, content.correct_answer)
        answer_count += 1

    assert session.status == BattleStatus.WON
    assert session.monster_hp == 0
    assert answer_count >= 10
    assert session.xp_earned > 0
    assert session.gold_earned > 0


def test_battle_can_use_japanese_language() -> None:
    engine = BattleEngine(QuestionSelector(QUESTIONS))
    session = engine.start("Ciel", None, Difficulty.HELL, DisplayLanguage.JA)
    question = session.current_question

    assert question is not None
    assert session.jlpt_level is None
    assert session.player_name == "Ciel"
    assert session.difficulty == Difficulty.HELL
    assert session.language == DisplayLanguage.JA

    content = get_localized_content(question, session.language)
    is_correct, _, _, explanation = engine.answer(
        session,
        question.id,
        content.correct_answer,
    )

    assert is_correct is True
    assert explanation is not None
