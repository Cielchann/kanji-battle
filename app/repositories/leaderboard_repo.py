from app.db.models import current_week_start
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import ScoreRecord
from app.models.enums import Difficulty, JlptLevel
from app.schemas.leaderboard import LeaderboardEntry


class LeaderboardRepository:
    def list(
        self,
        db: Session,
        jlpt_level: JlptLevel | None = None,
        difficulty: Difficulty | None = None,
        limit: int = 10,
        current_week_only: bool = True,
    ) -> list[LeaderboardEntry]:
        stmt = select(ScoreRecord).order_by(
            desc(ScoreRecord.score),
            desc(ScoreRecord.max_combo),
            ScoreRecord.created_at,
        )
        if jlpt_level is not None:
            stmt = stmt.where(ScoreRecord.jlpt_level == jlpt_level.value)
        if difficulty is not None:
            stmt = stmt.where(ScoreRecord.difficulty == difficulty.value)
        if current_week_only:
            stmt = stmt.where(ScoreRecord.week_start == current_week_start())

        records = db.scalars(stmt).all()
        entries: list[LeaderboardEntry] = []
        seen_player_names: set[str] = set()
        for record in records:
            if record.player_name in seen_player_names:
                continue
            seen_player_names.add(record.player_name)
            entries.append(
                LeaderboardEntry(
                    rank=len(entries) + 1,
                    player_name=record.player_name,
                    jlpt_level=JlptLevel(record.jlpt_level) if record.jlpt_level else None,
                    difficulty=Difficulty(record.difficulty),
                    score=record.score,
                    max_combo=record.max_combo,
                    xp_earned=record.xp_earned,
                    gold_earned=record.gold_earned,
                    week_start=record.week_start.isoformat(),
                )
            )
            if len(entries) >= limit:
                break
        return entries
