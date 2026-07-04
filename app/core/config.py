from functools import lru_cache
from os import getenv
from pathlib import Path

from pydantic import BaseModel


def load_local_env() -> None:
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_file.exists():
        return

    from os import environ

    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        environ.setdefault(key, value)


load_local_env()


class Settings(BaseModel):
    app_name: str = getenv("APP_NAME", "JLPT Kanji Battle Online")
    app_env: str = getenv("APP_ENV", "local")
    database_url: str = getenv("DATABASE_URL", "sqlite:///./jlpt_battle.db")
    auto_create_tables: bool = getenv("AUTO_CREATE_TABLES", "true").lower() == "true"
    kanji_api_base_url: str = getenv("KANJI_API_BASE_URL", "https://kanjiapi.dev/v1")
    admin_import_token: str = getenv("ADMIN_IMPORT_TOKEN", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
