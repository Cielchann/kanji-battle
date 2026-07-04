import socket
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
    if getenv("NEON_FORCE_IPV4", "false").lower() in {"1", "true", "yes"}:
        ipv4_hostaddr = _resolve_ipv4(parsed.hostname)
        if ipv4_hostaddr is not None:
            query_items.setdefault("hostaddr", ipv4_hostaddr)

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


def _resolve_ipv4(hostname: str) -> str | None:
    try:
        addresses = socket.getaddrinfo(hostname, 5432, socket.AF_INET, socket.SOCK_STREAM)
    except OSError:
        return None
    for address in addresses:
        ip_address = address[4][0]
        if ip_address:
            return ip_address
    return None
