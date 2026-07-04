from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.db.models import KanjiEntryRecord
from app.db.session import SessionLocal, create_db_and_tables
from app.repositories.kanji_repo import KanjiRepository
from app.repositories.question_repo import QuestionRepository
from app.services.kanji_api import KanjiApiClient, KanjiApiError
from app.services.kanji_question_factory import generate_questions_from_kanji
from sqlalchemy import select


def fetch_level_characters(level: int) -> list[str]:
    base_url = get_settings().kanji_api_base_url.rstrip("/")
    request = Request(
        f"{base_url}/kanji/jlpt-{level}",
        headers={"User-Agent": "JLPT-Kanji-Battle/0.1"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        msg = f"Failed to fetch JLPT N{level} kanji list."
        raise RuntimeError(msg) from exc

    return [character for character in payload if isinstance(character, str) and len(character) == 1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import JLPT kanji from KanjiAPI.dev.")
    parser.add_argument(
        "--levels",
        nargs="+",
        type=int,
        default=[5, 4, 3, 2, 1],
        choices=[1, 2, 3, 4, 5],
        help="JLPT numeric levels to import. Example: --levels 5 4 3",
    )
    parser.add_argument(
        "--max-new",
        type=int,
        default=0,
        help="Stop after this many newly imported kanji. 0 means no limit.",
    )
    parser.add_argument("--refresh", action="store_true", help="Refetch existing cached kanji.")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay between API detail requests.")
    parser.add_argument("--workers", type=int, default=6, help="Parallel API detail requests.")
    parser.add_argument(
        "--skip-create-tables",
        action="store_true",
        help="Do not call create_all before importing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.skip_create_tables and get_settings().auto_create_tables:
        create_db_and_tables()

    repository = KanjiRepository()

    seen: set[str] = set()
    characters: list[str] = []
    for level in args.levels:
        level_characters = fetch_level_characters(level)
        print(f"level=N{level} listed={len(level_characters)}", flush=True)
        for character in level_characters:
            if character not in seen:
                seen.add(character)
                characters.append(character)

    imported = 0
    cached = 0
    failed: list[str] = []

    with SessionLocal() as db:
        existing_characters = set(db.scalars(select(KanjiEntryRecord.character)).all())
        pending = [
            character
            for character in characters
            if args.refresh or character not in existing_characters
        ]
        cached = len(characters) - len(pending)
        if args.max_new:
            pending = pending[: args.max_new]

        print(f"pending={len(pending)} cached={cached}", flush=True)

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            future_to_character = {
                executor.submit(KanjiApiClient().fetch_kanji, character): character
                for character in pending
            }
            for future in as_completed(future_to_character):
                character = future_to_character[future]
                try:
                    entry = future.result()
                except KanjiApiError:
                    failed.append(character)
                    print(f"failed={len(failed)} imported={imported}", flush=True)
                    continue

                repository.save(db, entry)
                imported += 1
                if imported % 25 == 0 or imported == len(pending):
                    print(
                        f"imported={imported}/{len(pending)} cached={cached} failed={len(failed)}",
                        flush=True,
                    )
                if args.delay > 0:
                    time.sleep(args.delay)

        cached_entries = repository.list(db, limit=10_000)
        generated_questions = generate_questions_from_kanji(cached_entries)
        QuestionRepository().upsert_many(db, generated_questions)

    print(f"done imported={imported}", flush=True)
    print(f"done cached={cached}", flush=True)
    print(f"done failed={len(failed)}", flush=True)
    print(f"done generated_questions={len(generated_questions)}", flush=True)


if __name__ == "__main__":
    main()
