from __future__ import annotations

from time import sleep

import psycopg

from app.core.config import get_settings
from app.db.url import normalize_database_url


PATTERNS = [
    "NeonQA-%",
    "FLOW-%",
    "JA-%",
    "LB-%",
    "SHOP-%",
    "UL-%",
    "LOCK-%",
    "BEST-%",
    "QA-%",
    "QA-detail-%",
    "QA-lock-%",
    "RANDOM-CHECK-%",
]


def connect():
    dsn = normalize_database_url(get_settings().database_url).replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )
    last_error: Exception | None = None
    for attempt in range(1, 8):
        print(f"cleanup_connect_attempt={attempt}", flush=True)
        try:
            return psycopg.connect(dsn, connect_timeout=8)
        except psycopg.OperationalError as exc:
            last_error = exc
            sleep(3)
    if last_error is not None:
        raise last_error
    raise RuntimeError("Connection failed.")


def where_clause(column: str = "player_name") -> str:
    return " or ".join([f"{column} like %s" for _ in PATTERNS])


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"select id from battle_sessions where {where_clause()}",
                PATTERNS,
            )
            battle_ids = [row[0] for row in cur.fetchall()]
            cur.execute(
                f"select battle_id from scores where {where_clause()}",
                PATTERNS,
            )
            battle_ids.extend(row[0] for row in cur.fetchall())
            battle_ids = sorted(set(battle_ids))

            if battle_ids:
                cur.execute(
                    "delete from battle_turns where battle_id = any(%s)",
                    (battle_ids,),
                )
                cur.execute(
                    "delete from scores where battle_id = any(%s)",
                    (battle_ids,),
                )
                cur.execute(
                    "delete from battle_sessions where id = any(%s)",
                    (battle_ids,),
                )

            for table in ["difficulty_progress", "player_weapons", "player_profiles"]:
                cur.execute(
                    f"delete from {table} where {where_clause()}",
                    PATTERNS,
                )
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("select count(*) from player_profiles")
            print(f"player_profiles={cur.fetchone()[0]}", flush=True)
            cur.execute("select count(*) from scores")
            print(f"scores={cur.fetchone()[0]}", flush=True)


if __name__ == "__main__":
    main()
