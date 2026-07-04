from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_leaderboard_repository
from app.db.session import get_db
from app.models.enums import Difficulty, JlptLevel
from app.repositories.leaderboard_repo import LeaderboardRepository
from app.schemas.leaderboard import LeaderboardEntry

router = APIRouter()


@router.get("", response_model=list[LeaderboardEntry])
def list_leaderboard(
    jlpt_level: JlptLevel | None = None,
    difficulty: Difficulty | None = None,
    limit: int = 10,
    current_week_only: bool = True,
    db: Session = Depends(get_db),
    repository: LeaderboardRepository = Depends(get_leaderboard_repository),
) -> list[LeaderboardEntry]:
    return repository.list(
        db,
        jlpt_level=jlpt_level,
        difficulty=difficulty,
        limit=limit,
        current_week_only=current_week_only,
    )
