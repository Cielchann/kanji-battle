from pydantic import BaseModel, Field

from app.models.enums import BattleStatus, Difficulty, DisplayLanguage, JlptLevel
from app.schemas.question import PublicQuestion


class Monster(BaseModel):
    name: str
    max_hp: int = Field(gt=0)
    hp: int = Field(ge=0)


class BattleState(BaseModel):
    battle_id: str
    player_name: str
    jlpt_level: JlptLevel | None
    difficulty: Difficulty
    language: DisplayLanguage
    player_hp: int = Field(ge=0)
    monster: Monster
    weapon_name: str | None = None
    weapon_attack_bonus: int = Field(ge=0)
    combo: int = Field(ge=0)
    score: int = Field(ge=0)
    xp_earned: int = Field(ge=0)
    gold_earned: int = Field(ge=0)
    turn: int = Field(ge=1)
    status: BattleStatus
    current_question: PublicQuestion | None = None


class StartBattleRequest(BaseModel):
    player_name: str = Field(default="Guest Player", min_length=1, max_length=40)
    device_token: str = Field(min_length=16, max_length=128)
    jlpt_level: JlptLevel | None = None
    difficulty: Difficulty = Difficulty.EASY
    language: DisplayLanguage = DisplayLanguage.EN


class AnswerRequest(BaseModel):
    battle_id: str
    question_id: int
    answer: str


class AnswerResult(BaseModel):
    is_correct: bool
    damage_dealt: int
    damage_taken: int
    explanation: str | None
    state: BattleState
