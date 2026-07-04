from os import getenv
from time import sleep
from urllib.parse import urlsplit

import psycopg
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.db.url import normalize_database_url


def create_database_engine(database_url: str) -> Engine:
    normalized_url = normalize_database_url(database_url)
    connect_args = {"check_same_thread": False} if normalized_url.startswith("sqlite") else {}

    if _is_neon_url(normalized_url):
        psycopg_dsn = normalized_url.replace("postgresql+psycopg://", "postgresql://", 1)
        return create_engine(
            "postgresql+psycopg://",
            creator=lambda: _connect_with_retry(psycopg_dsn),
            pool_pre_ping=True,
        )

    return create_engine(normalized_url, connect_args=connect_args, pool_pre_ping=True)


def _is_neon_url(database_url: str) -> bool:
    parsed = urlsplit(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
    return parsed.hostname is not None and parsed.hostname.endswith(".neon.tech")


def _connect_with_retry(dsn: str) -> psycopg.Connection:
    last_error: psycopg.OperationalError | None = None
    retries = max(1, int(getenv("DB_CONNECT_RETRIES", "8")))
    for attempt in range(1, retries + 1):
        try:
            return psycopg.connect(dsn)
        except psycopg.OperationalError as exc:
            last_error = exc
            sleep(min(attempt * 2, 8))
    if last_error is None:
        raise RuntimeError("Database connection failed.")
    raise last_error
