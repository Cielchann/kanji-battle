from pydantic import BaseModel, Field

from app.models.enums import Difficulty


class DifficultyProgress(BaseModel):
    difficulty: Difficulty
    clears: int = Field(ge=0)
    perfect_clears: int = Field(ge=0)
    unlocked: bool
    locked_reason: str | None = None


class PlayerProgress(BaseModel):
    player_name: str
    hero_role: str
    xp: int = Field(ge=0)
    gold: int = Field(ge=0)
    total_clears: int = Field(ge=0)
    difficulties: list[DifficultyProgress]

