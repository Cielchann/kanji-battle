from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DifficultyProgressRecord, PlayerProfileRecord
from app.models.enums import BattleStatus, Difficulty
from app.schemas.progress import DifficultyProgress, PlayerProgress
from app.services.battle_engine import BattleSession
from app.services.battle_balance import PLAYER_HP_BY_DIFFICULTY
from app.services.unlocks import get_locked_reason


class PlayerNameTakenError(ValueError):
    pass


class ProgressRepository:
    def get_or_create_profile(
        self,
        db: Session,
        player_name: str,
        owner_token: str | None = None,
    ) -> PlayerProfileRecord:
        profile = db.get(PlayerProfileRecord, player_name)
        if profile is None:
            profile = PlayerProfileRecord(
                player_name=player_name,
                owner_token=owner_token,
                hero_role="Hero",
                xp=0,
                gold=0,
                total_clears=0,
            )
            db.add(profile)
            db.commit()
            return profile

        if owner_token is None:
            return profile

        if profile.owner_token is None:
            profile.owner_token = owner_token
            db.commit()
            return profile

        if profile.owner_token != owner_token:
            raise PlayerNameTakenError(
                "This player name is already used on another device."
            )
        return profile

    def get_perfect_clears_by_difficulty(
        self,
        db: Session,
        player_name: str,
    ) -> dict[Difficulty, int]:
        records = db.scalars(
            select(DifficultyProgressRecord).where(
                DifficultyProgressRecord.player_name == player_name
            )
        ).all()
        return {
            Difficulty(record.difficulty): record.perfect_clears
            for record in records
        }

    def get_progress(
        self,
        db: Session,
        player_name: str,
        owner_token: str | None = None,
    ) -> PlayerProgress:
        profile = self.get_or_create_profile(db, player_name, owner_token)
        records = db.scalars(
            select(DifficultyProgressRecord).where(
                DifficultyProgressRecord.player_name == player_name
            )
        ).all()
        records_by_difficulty = {
            Difficulty(record.difficulty): record
            for record in records
        }
        perfect_clears = self.get_perfect_clears_by_difficulty(db, player_name)

        difficulties: list[DifficultyProgress] = []
        for difficulty in Difficulty:
            record = records_by_difficulty.get(difficulty)
            locked_reason = get_locked_reason(difficulty, perfect_clears)
            difficulties.append(
                DifficultyProgress(
                    difficulty=difficulty,
                    clears=record.clears if record is not None else 0,
                    perfect_clears=record.perfect_clears if record is not None else 0,
                    unlocked=locked_reason is None,
                    locked_reason=locked_reason,
                )
            )

        return PlayerProgress(
            player_name=profile.player_name,
            hero_role=profile.hero_role,
            xp=profile.xp,
            gold=profile.gold,
            total_clears=profile.total_clears,
            difficulties=difficulties,
        )

    def record_finished_battle(self, db: Session, session: BattleSession) -> None:
        if session.status != BattleStatus.WON:
            return

        profile = self.get_or_create_profile(db, session.player_name)
        profile.xp += session.xp_earned
        profile.gold += session.gold_earned
        profile.total_clears += 1

        progress = db.scalar(
            select(DifficultyProgressRecord).where(
                DifficultyProgressRecord.player_name == session.player_name,
                DifficultyProgressRecord.difficulty == session.difficulty.value,
            )
        )
        if progress is None:
            progress = DifficultyProgressRecord(
                player_name=session.player_name,
                difficulty=session.difficulty.value,
                clears=0,
                perfect_clears=0,
            )
            db.add(progress)

        progress.clears += 1
        if session.player_hp == PLAYER_HP_BY_DIFFICULTY[session.difficulty]:
            progress.perfect_clears += 1

        db.commit()
