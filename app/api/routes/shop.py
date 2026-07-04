from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_progress_repository, get_shop_repository
from app.db.session import get_db
from app.repositories.progress_repo import PlayerNameTakenError, ProgressRepository
from app.repositories.shop_repo import ShopRepository
from app.schemas.shop import BuyWeaponRequest, EquipWeaponRequest, Weapon, WeaponActionResult

router = APIRouter()


@router.get("/weapons", response_model=list[Weapon])
def list_weapons(
    player_name: str,
    device_token: str = Query(min_length=16, max_length=128),
    db: Session = Depends(get_db),
    progress_repository: ProgressRepository = Depends(get_progress_repository),
    shop_repository: ShopRepository = Depends(get_shop_repository),
) -> list[Weapon]:
    try:
        progress_repository.get_or_create_profile(db, player_name, device_token)
    except PlayerNameTakenError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return shop_repository.list_weapons(db, player_name)


@router.post("/buy", response_model=WeaponActionResult)
def buy_weapon(
    payload: BuyWeaponRequest,
    db: Session = Depends(get_db),
    progress_repository: ProgressRepository = Depends(get_progress_repository),
    shop_repository: ShopRepository = Depends(get_shop_repository),
) -> WeaponActionResult:
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
    try:
        return shop_repository.buy_weapon(db, payload.player_name, payload.weapon_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/equip", response_model=WeaponActionResult)
def equip_weapon(
    payload: EquipWeaponRequest,
    db: Session = Depends(get_db),
    progress_repository: ProgressRepository = Depends(get_progress_repository),
    shop_repository: ShopRepository = Depends(get_shop_repository),
) -> WeaponActionResult:
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
    try:
        return shop_repository.equip_weapon(db, payload.player_name, payload.weapon_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
