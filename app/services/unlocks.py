from app.models.enums import Difficulty


BASE_UNLOCKED_DIFFICULTIES = {
    Difficulty.EASY,
    Difficulty.MEDIUM,
    Difficulty.HARD,
}


def get_locked_reason(
    difficulty: Difficulty,
    perfect_clears_by_difficulty: dict[Difficulty, int],
) -> str | None:
    if difficulty in BASE_UNLOCKED_DIFFICULTIES:
        return None

    hard_perfect_clears = perfect_clears_by_difficulty.get(Difficulty.HARD, 0)
    if difficulty == Difficulty.EXTREME and hard_perfect_clears < 2:
        return "Extreme unlocks after 2 perfect clears on Hard."

    if difficulty == Difficulty.HELL:
        required_difficulties = [
            Difficulty.EASY,
            Difficulty.MEDIUM,
            Difficulty.HARD,
            Difficulty.EXTREME,
        ]
        missing = [
            item.value
            for item in required_difficulties
            if perfect_clears_by_difficulty.get(item, 0) < 1
        ]
        if missing:
            return (
                "Hell unlocks after 1 perfect clear on each difficulty: "
                + ", ".join(missing)
                + "."
            )

    return None
