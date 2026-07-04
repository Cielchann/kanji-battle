from app.models.enums import Difficulty


MONSTER_HP_BY_DIFFICULTY: dict[Difficulty, int] = {
    Difficulty.EASY: 100_000,
    Difficulty.MEDIUM: 250_000,
    Difficulty.HARD: 600_000,
    Difficulty.EXTREME: 1_200_000,
    Difficulty.HELL: 2_400_000,
}


PLAYER_HP_BY_DIFFICULTY: dict[Difficulty, int] = {
    Difficulty.EASY: 100_000,
    Difficulty.MEDIUM: 250_000,
    Difficulty.HARD: 600_000,
    Difficulty.EXTREME: 1_200_000,
    Difficulty.HELL: 2_400_000,
}
