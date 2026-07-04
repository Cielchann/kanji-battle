from app.data.starter_kanji import STARTER_KANJI_PACK
from app.core.config import get_settings
from app.db.session import SessionLocal, create_db_and_tables
from app.repositories.kanji_repo import KanjiRepository
from app.services.kanji_api import KanjiApiClient, KanjiApiError


def main() -> None:
    if get_settings().auto_create_tables:
        create_db_and_tables()
    repository = KanjiRepository()
    client = KanjiApiClient()
    imported = 0
    cached = 0
    failed: list[str] = []

    with SessionLocal() as db:
        for character in STARTER_KANJI_PACK:
            if repository.get(db, character) is not None:
                cached += 1
                continue
            try:
                entry = client.fetch_kanji(character)
            except KanjiApiError:
                failed.append(character)
                continue
            repository.save(db, entry)
            imported += 1

    print(f"imported={imported}")
    print(f"cached={cached}")
    print(f"failed={failed}")


if __name__ == "__main__":
    main()
