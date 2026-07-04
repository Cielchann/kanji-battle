from dataclasses import dataclass

from app.models.enums import Difficulty


@dataclass(frozen=True)
class BattleReward:
    xp: int
    gold: int


REWARD_BY_DIFFICULTY: dict[Difficulty, BattleReward] = {
    Difficulty.EASY: BattleReward(xp=20, gold=10),
    Difficulty.MEDIUM: BattleReward(xp=40, gold=20),
    Difficulty.HARD: BattleReward(xp=70, gold=35),
    Difficulty.EXTREME: BattleReward(xp=120, gold=60),
    Difficulty.HELL: BattleReward(xp=200, gold=100),
}


def calculate_clear_reward(difficulty: Difficulty, is_perfect_clear: bool) -> BattleReward:
    base_reward = REWARD_BY_DIFFICULTY[difficulty]
    if not is_perfect_clear:
        return base_reward
    return BattleReward(
        xp=base_reward.xp + base_reward.xp // 2,
        gold=base_reward.gold + base_reward.gold // 2,
    )

