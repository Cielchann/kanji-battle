from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BattleSessionRecord, BattleTurnRecord, ScoreRecord
from app.models.enums import BattleStatus, Difficulty, DisplayLanguage, JlptLevel
from app.repositories.question_repo import QuestionRepository
from app.services.battle_engine import BattleSession


class BattleRepository:
    def __init__(self, question_repository: QuestionRepository) -> None:
        self._question_repository = question_repository

    def save(self, db: Session, session: BattleSession) -> BattleSession:
        record = db.get(BattleSessionRecord, session.battle_id)
        current_question_id = (
            session.current_question.id if session.current_question is not None else None
        )
        ended_at = (
            datetime.now(timezone.utc)
            if session.status != BattleStatus.IN_PROGRESS
            else None
        )

        if record is None:
            record = BattleSessionRecord(
                id=session.battle_id,
                player_name=session.player_name,
                jlpt_level=session.jlpt_level.value if session.jlpt_level is not None else None,
                difficulty=session.difficulty.value,
                language=session.language.value,
                player_hp=session.player_hp,
                monster_name=session.monster_name,
                monster_max_hp=session.monster_max_hp,
                monster_hp=session.monster_hp,
                weapon_name=session.weapon_name,
                weapon_attack_bonus=session.weapon_attack_bonus,
                combo=session.combo,
                max_combo=session.max_combo,
                score=session.score,
                xp_earned=session.xp_earned,
                gold_earned=session.gold_earned,
                turn=session.turn,
                status=session.status.value,
                current_question_id=current_question_id,
                used_question_ids=sorted(session.used_question_ids),
                ended_at=ended_at,
            )
            db.add(record)
        else:
            record.player_name = session.player_name
            record.jlpt_level = session.jlpt_level.value if session.jlpt_level is not None else None
            record.difficulty = session.difficulty.value
            record.language = session.language.value
            record.player_hp = session.player_hp
            record.monster_name = session.monster_name
            record.monster_max_hp = session.monster_max_hp
            record.monster_hp = session.monster_hp
            record.weapon_name = session.weapon_name
            record.weapon_attack_bonus = session.weapon_attack_bonus
            record.combo = session.combo
            record.max_combo = session.max_combo
            record.score = session.score
            record.xp_earned = session.xp_earned
            record.gold_earned = session.gold_earned
            record.turn = session.turn
            record.status = session.status.value
            record.current_question_id = current_question_id
            record.used_question_ids = sorted(session.used_question_ids)
            if record.ended_at is None:
                record.ended_at = ended_at

        db.commit()
        return session

    def get(self, db: Session, battle_id: str) -> BattleSession | None:
        record = db.get(BattleSessionRecord, battle_id)
        if record is None:
            return None

        current_question = None
        if record.current_question_id is not None:
            current_question = self._question_repository.get(db, record.current_question_id)

        return BattleSession(
            battle_id=record.id,
            player_name=record.player_name,
            jlpt_level=JlptLevel(record.jlpt_level) if record.jlpt_level is not None else None,
            difficulty=Difficulty(record.difficulty),
            language=DisplayLanguage(record.language),
            player_hp=record.player_hp,
            monster_name=record.monster_name,
            monster_max_hp=record.monster_max_hp,
            monster_hp=record.monster_hp,
            weapon_name=record.weapon_name,
            weapon_attack_bonus=record.weapon_attack_bonus,
            combo=record.combo,
            max_combo=record.max_combo,
            score=record.score,
            xp_earned=record.xp_earned,
            gold_earned=record.gold_earned,
            turn=record.turn,
            status=BattleStatus(record.status),
            current_question=current_question,
            used_question_ids=set(record.used_question_ids),
        )

    def add_turn(
        self,
        db: Session,
        session: BattleSession,
        question_id: int,
        answer: str,
        is_correct: bool,
        damage_dealt: int,
        damage_taken: int,
    ) -> None:
        db.add(
            BattleTurnRecord(
                battle_id=session.battle_id,
                question_id=question_id,
                user_answer=answer,
                is_correct=is_correct,
                damage_dealt=damage_dealt,
                damage_taken=damage_taken,
            )
        )
        db.commit()

    def save_score_if_finished(self, db: Session, session: BattleSession) -> bool:
        if session.status == BattleStatus.IN_PROGRESS:
            return False

        existing = db.scalar(
            select(ScoreRecord).where(ScoreRecord.battle_id == session.battle_id)
        )
        if existing is not None:
            return False

        db.add(
            ScoreRecord(
                battle_id=session.battle_id,
                player_name=session.player_name,
                jlpt_level=session.jlpt_level.value if session.jlpt_level is not None else None,
                difficulty=session.difficulty.value,
                score=session.score,
                max_combo=session.max_combo,
                xp_earned=session.xp_earned,
                gold_earned=session.gold_earned,
                status=session.status.value,
            )
        )
        db.commit()
        return True
