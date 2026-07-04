import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.schemas.kanji import KanjiEntry
from app.services.kanji_power import calculate_kanji_power


class KanjiApiError(RuntimeError):
    pass


class KanjiApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.kanji_api_base_url).rstrip("/")

    def fetch_kanji(self, character: str) -> KanjiEntry:
        safe_character = quote(character, safe="")
        request = Request(
            f"{self._base_url}/kanji/{safe_character}",
            headers={"User-Agent": "JLPT-Kanji-Battle/0.1"},
        )
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            msg = f"Kanji API returned HTTP {exc.code} for {character}."
            raise KanjiApiError(msg) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            msg = f"Kanji API request failed for {character}."
            raise KanjiApiError(msg) from exc

        power = calculate_kanji_power(
            jlpt=payload.get("jlpt"),
            grade=payload.get("grade"),
            stroke_count=payload.get("stroke_count"),
        )
        return KanjiEntry(
            character=payload["kanji"],
            meanings=payload.get("meanings", []),
            kun_readings=payload.get("kun_readings", []),
            on_readings=payload.get("on_readings", []),
            name_readings=payload.get("name_readings", []),
            stroke_count=payload.get("stroke_count"),
            grade=payload.get("grade"),
            jlpt=payload.get("jlpt"),
            unicode=payload.get("unicode"),
            power=power,
            source="kanjiapi.dev",
        )
