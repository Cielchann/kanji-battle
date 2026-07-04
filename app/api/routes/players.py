from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_progress_repository
from app.db.session import get_db
from app.repositories.progress_repo import PlayerNameTakenError, ProgressRepository
from app.schemas.progress import PlayerProgress

router = APIRouter()


@router.get("/{player_name}/progress", response_model=PlayerProgress)
def get_player_progress(
    player_name: str,
    device_token: str = Query(min_length=16, max_length=128),
    db: Session = Depends(get_db),
    repository: ProgressRepository = Depends(get_progress_repository),
) -> PlayerProgress:
    try:
        return repository.get_progress(db, player_name, device_token)
    except PlayerNameTakenError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
