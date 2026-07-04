from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_kanji_api_client, get_kanji_repository
from app.core.config import get_settings
from app.data.starter_kanji import STARTER_KANJI_PACK
from app.db.session import get_db
from app.repositories.kanji_repo import KanjiRepository
from app.repositories.question_repo import QuestionRepository
from app.schemas.kanji import ImportKanjiRequest, ImportKanjiResult, KanjiEntry
from app.services.kanji_api import KanjiApiClient, KanjiApiError
from app.services.kanji_question_factory import generate_questions_from_kanji

router = APIRouter()


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    expected_token = get_settings().admin_import_token
    if not expected_token:
        return
    if x_admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token.",
        )


@router.get("/{character}", response_model=KanjiEntry)
def get_kanji(
    character: str,
    refresh: bool = False,
    db: Session = Depends(get_db),
    repository: KanjiRepository = Depends(get_kanji_repository),
    client: KanjiApiClient = Depends(get_kanji_api_client),
) -> KanjiEntry:
    if len(character) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please request exactly one kanji character.",
        )

    cached = repository.get(db, character)
    if cached is not None and not refresh:
        return cached

    try:
        entry = client.fetch_kanji(character)
    except KanjiApiError as exc:
        if cached is not None:
            return cached
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return repository.save(db, entry)


@router.post("/import", response_model=ImportKanjiResult)
def import_kanji(
    payload: ImportKanjiRequest,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
    repository: KanjiRepository = Depends(get_kanji_repository),
    client: KanjiApiClient = Depends(get_kanji_api_client),
) -> ImportKanjiResult:
    imported = 0
    cached = 0
    failed: list[str] = []

    for character in dict.fromkeys(payload.characters):
        if len(character) != 1:
            failed.append(character)
            continue

        existing = repository.get(db, character)
        if existing is not None and not payload.refresh:
            cached += 1
            continue

        try:
            entry = client.fetch_kanji(character)
        except KanjiApiError:
            failed.append(character)
            continue

        repository.save(db, entry)
        imported += 1

    if imported > 0:
        cached_kanji = repository.list(db, limit=10_000)
        generated_questions = generate_questions_from_kanji(cached_kanji)
        QuestionRepository().upsert_many(db, generated_questions)

    return ImportKanjiResult(imported=imported, cached=cached, failed=failed)


@router.post("/import/starter", response_model=ImportKanjiResult)
def import_starter_kanji(
    refresh: bool = False,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
    repository: KanjiRepository = Depends(get_kanji_repository),
    client: KanjiApiClient = Depends(get_kanji_api_client),
) -> ImportKanjiResult:
    return import_kanji(
        ImportKanjiRequest(characters=STARTER_KANJI_PACK, refresh=refresh),
        _,
        db,
        repository,
        client,
    )
