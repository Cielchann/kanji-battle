from pydantic import BaseModel, Field

from app.models.enums import Difficulty, JlptLevel


class LeaderboardEntry(BaseModel):
    rank: int = Field(ge=1)
    player_name: str
    jlpt_level: JlptLevel | None
    difficulty: Difficulty | None
    score: int = Field(ge=0)
    max_combo: int = Field(ge=0)
    xp_earned: int = Field(ge=0)
    gold_earned: int = Field(ge=0)
    week_start: str
