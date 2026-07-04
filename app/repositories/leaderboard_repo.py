from app.db.models import current_week_start
from sqlalchemy import desc, func, select
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
        total_score = func.sum(ScoreRecord.score).label("total_score")
        best_combo = func.max(ScoreRecord.max_combo).label("best_combo")
        total_xp = func.sum(ScoreRecord.xp_earned).label("total_xp")
        total_gold = func.sum(ScoreRecord.gold_earned).label("total_gold")
        first_week_start = func.min(ScoreRecord.week_start).label("week_start")

        stmt = select(
            ScoreRecord.player_name,
            ScoreRecord.jlpt_level,
            ScoreRecord.difficulty,
            total_score,
            best_combo,
            total_xp,
            total_gold,
            first_week_start,
        ).group_by(
            ScoreRecord.player_name,
            ScoreRecord.jlpt_level,
            ScoreRecord.difficulty,
            ScoreRecord.week_start,
        )
        if jlpt_level is not None:
            stmt = stmt.where(ScoreRecord.jlpt_level == jlpt_level.value)
        if difficulty is not None:
            stmt = stmt.where(ScoreRecord.difficulty == difficulty.value)
        if current_week_only:
            stmt = stmt.where(ScoreRecord.week_start == current_week_start())

        stmt = stmt.order_by(desc(total_score), desc(best_combo), ScoreRecord.player_name).limit(limit)
        records = db.execute(stmt).all()
        entries: list[LeaderboardEntry] = []
        for record in records:
            entries.append(
                LeaderboardEntry(
                    rank=len(entries) + 1,
                    player_name=record.player_name,
                    jlpt_level=JlptLevel(record.jlpt_level) if record.jlpt_level else None,
                    difficulty=Difficulty(record.difficulty),
                    score=int(record.total_score or 0),
                    max_combo=int(record.best_combo or 0),
                    xp_earned=int(record.total_xp or 0),
                    gold_earned=int(record.total_gold or 0),
                    week_start=record.week_start.isoformat(),
                )
            )
        return entries
