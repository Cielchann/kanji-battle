BASE_SCORE = 80
POWER_SCORE_BONUS = 20
COMBO_SCORE_BONUS = 25


def calculate_damage(
    monster_max_hp: int,
    combo: int,
    question_power: int,
    weapon_attack_bonus: int = 0,
) -> int:
    base_damage = monster_max_hp // 10
    power_multiplier = 0.80 + (question_power * 0.08)
    combo_multiplier = 1 + min(combo, 8) * 0.03
    weapon_multiplier = 1 + (weapon_attack_bonus / 100)
    return max(1, round(base_damage * power_multiplier * combo_multiplier * weapon_multiplier))


def calculate_score_gain(combo: int, question_power: int) -> int:
    return BASE_SCORE + (question_power * POWER_SCORE_BONUS) + (combo * COMBO_SCORE_BONUS)


def calculate_wrong_answer_damage(player_max_hp: int, question_power: int) -> int:
    base_damage = player_max_hp // 10
    power_multiplier = 0.70 + (question_power * 0.06)
    return max(1, round(base_damage * power_multiplier))
