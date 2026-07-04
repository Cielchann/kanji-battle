from __future__ import annotations

from time import sleep

import psycopg

from app.core.config import get_settings
from app.db.url import normalize_database_url


def main() -> None:
    dsn = normalize_database_url(get_settings().database_url).replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )
    last_error: Exception | None = None
    for attempt in range(1, 8):
        print(f"verify_attempt={attempt}", flush=True)
        try:
            with psycopg.connect(dsn, connect_timeout=8) as conn:
                with conn.cursor() as cur:
                    cur.execute("set statement_timeout = 15000")
                    for table in [
                        "kanji_entries",
                        "questions",
                        "weapons",
                        "player_profiles",
                        "scores",
                    ]:
                        cur.execute(f"select count(*) from {table}")
                        print(f"{table}={cur.fetchone()[0]}", flush=True)
                    cur.execute(
                        "select count(*) from information_schema.columns "
                        "where table_name='player_profiles' "
                        "and column_name='owner_token'"
                    )
                    print(f"owner_token_column={cur.fetchone()[0] == 1}", flush=True)
                    return
        except Exception as exc:
            last_error = exc
            print(f"verify_fail={type(exc).__name__}", flush=True)
            sleep(3)
    if last_error is not None:
        raise last_error


if __name__ == "__main__":
    main()
