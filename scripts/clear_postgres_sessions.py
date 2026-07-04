from __future__ import annotations

from time import sleep

import psycopg

from app.core.config import get_settings
from app.db.url import normalize_database_url


def connect():
    dsn = normalize_database_url(get_settings().database_url).replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )
    last_error: Exception | None = None
    for attempt in range(1, 8):
        print(f"connect_attempt={attempt}", flush=True)
        try:
            return psycopg.connect(dsn, connect_timeout=8)
        except psycopg.OperationalError as exc:
            last_error = exc
            sleep(3)
    if last_error is not None:
        raise last_error
    raise RuntimeError("Connection failed.")


def main() -> None:
    with connect() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                """
                select pid
                from pg_stat_activity
                where datname = current_database()
                  and pid <> pg_backend_pid()
                """
            )
            pids = [row[0] for row in cur.fetchall()]
            print(f"other_sessions={len(pids)}", flush=True)
            for pid in pids:
                cur.execute("select pg_terminate_backend(%s)", (pid,))
                print(f"terminated={pid}:{cur.fetchone()[0]}", flush=True)


if __name__ == "__main__":
    main()
