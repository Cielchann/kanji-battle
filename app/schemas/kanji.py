from pydantic import BaseModel, Field


class KanjiEntry(BaseModel):
    character: str = Field(min_length=1, max_length=8)
    meanings: list[str]
    kun_readings: list[str]
    on_readings: list[str]
    name_readings: list[str] = []
    stroke_count: int | None = None
    grade: int | None = None
    jlpt: int | None = None
    unicode: str | None = None
    power: int = Field(ge=1, le=5)
    source: str = "kanjiapi.dev"


class ImportKanjiRequest(BaseModel):
    characters: list[str] = Field(min_length=1, max_length=100)
    refresh: bool = False


class ImportKanjiResult(BaseModel):
    imported: int
    cached: int
    failed: list[str]
