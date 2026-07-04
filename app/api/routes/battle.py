from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_battle_repository,
    get_kanji_repository,
    get_progress_repository,
    get_question_repository,
    get_shop_repository,
)
from app.db.session import get_db
from app.repositories.battle_repo import BattleRepository
from app.repositories.kanji_repo import KanjiRepository
from app.repositories.progress_repo import PlayerNameTakenError, ProgressRepository
from app.repositories.question_repo import QuestionRepository
from app.repositories.shop_repo import ShopRepository
from app.schemas.battle import AnswerRequest, AnswerResult, BattleState, StartBattleRequest
from app.services.battle_engine import BattleEngine, to_battle_state
from app.services.kanji_question_factory import KANJI_QUESTION_ID_OFFSET, generate_questions_from_kanji
from app.services.question_selector import QuestionSelector
from app.services.unlocks import get_locked_reason

router = APIRouter()


def load_battle_questions(
    db: Session,
    question_repository: QuestionRepository,
    kanji_repository: KanjiRepository,
):
    questions = question_repository.list(db)
    has_generated_kanji_questions = any(
        question.id >= KANJI_QUESTION_ID_OFFSET for question in questions
    )
    if has_generated_kanji_questions:
        return questions

    cached_kanji = kanji_repository.list(db, limit=10_000)
    generated_questions = generate_questions_from_kanji(cached_kanji)
    question_repository.upsert_many(db, generated_questions)
    return question_repository.list(db)


@router.post("/start", response_model=BattleState)
def start_battle(
    payload: StartBattleRequest,
    db: Session = Depends(get_db),
    question_repository: QuestionRepository = Depends(get_question_repository),
    kanji_repository: KanjiRepository = Depends(get_kanji_repository),
    battle_repository: BattleRepository = Depends(get_battle_repository),
    progress_repository: ProgressRepository = Depends(get_progress_repository),
    shop_repository: ShopRepository = Depends(get_shop_repository),
) -> BattleState:
    try:
        progress_repository.get_or_create_profile(
            db,
            payload.player_name,
            payload.device_token,
        )
    except PlayerNameTakenError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    shop_repository.grant_starter_weapon(db, payload.player_name)
    perfect_clears = progress_repository.get_perfect_clears_by_difficulty(
        db,
        payload.player_name,
    )
    locked_reason = get_locked_reason(payload.difficulty, perfect_clears)
    if locked_reason is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=locked_reason,
        )

    questions = load_battle_questions(db, question_repository, kanji_repository)
    engine = BattleEngine(QuestionSelector(questions))
    equipped_weapon = shop_repository.get_equipped_weapon(db, payload.player_name)
    try:
        session = engine.start(
            payload.player_name,
            None,
            payload.difficulty,
            payload.language,
            weapon_name=equipped_weapon.name if equipped_weapon is not None else None,
            weapon_attack_bonus=equipped_weapon.attack_bonus if equipped_weapon is not None else 0,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    battle_repository.save(db, session)
    return to_battle_state(session)


@router.post("/answer", response_model=AnswerResult)
def answer_question(
    payload: AnswerRequest,
    db: Session = Depends(get_db),
    question_repository: QuestionRepository = Depends(get_question_repository),
    kanji_repository: KanjiRepository = Depends(get_kanji_repository),
    battle_repository: BattleRepository = Depends(get_battle_repository),
    progress_repository: ProgressRepository = Depends(get_progress_repository),
) -> AnswerResult:
    session = battle_repository.get(db, payload.battle_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle session not found.",
        )

    questions = load_battle_questions(db, question_repository, kanji_repository)
    engine = BattleEngine(QuestionSelector(questions))
    was_in_progress = session.status.value == "in_progress"
    try:
        is_correct, damage_dealt, damage_taken, explanation = engine.answer(
            session,
            payload.question_id,
            payload.answer,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    battle_repository.save(db, session)
    battle_repository.add_turn(
        db,
        session,
        payload.question_id,
        payload.answer,
        is_correct,
        damage_dealt,
        damage_taken,
    )
    score_inserted = battle_repository.save_score_if_finished(db, session)
    if score_inserted and was_in_progress:
        progress_repository.record_finished_battle(db, session)
    return AnswerResult(
        is_correct=is_correct,
        damage_dealt=damage_dealt,
        damage_taken=damage_taken,
        explanation=explanation,
        state=to_battle_state(session),
    )


@router.get("/{battle_id}", response_model=BattleState)
def get_battle(
    battle_id: str,
    db: Session = Depends(get_db),
    repository: BattleRepository = Depends(get_battle_repository),
) -> BattleState:
    session = repository.get(db, battle_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle session not found.",
        )
    return to_battle_state(session)
