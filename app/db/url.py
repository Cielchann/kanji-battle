from os import getenv
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_database_url(database_url: str) -> str:
    database_url = _normalize_neon_ssl(database_url)
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return database_url


def _normalize_neon_ssl(database_url: str) -> str:
    parsed = urlsplit(database_url)
    if parsed.hostname is None or not parsed.hostname.endswith(".neon.tech"):
        return database_url

    query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_items.setdefault("sslmode", "require")
    query_items.setdefault("connect_timeout", getenv("NEON_CONNECT_TIMEOUT", "10"))

    return urlunsplit(
        (
            parsed.scheme,
            _with_default_postgres_port(parsed.netloc),
            parsed.path,
            urlencode(query_items),
            parsed.fragment,
        )
    )


def _with_default_postgres_port(netloc: str) -> str:
    credentials, separator, host = netloc.rpartition("@")
    if ":" in host:
        return netloc
    normalized_host = f"{host}:5432"
    if separator:
        return f"{credentials}@{normalized_host}"
    return normalized_host
