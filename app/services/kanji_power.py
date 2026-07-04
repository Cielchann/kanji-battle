def calculate_kanji_power(
    *,
    jlpt: int | None,
    grade: int | None,
    stroke_count: int | None,
) -> int:
    if jlpt == 5:
        return 1
    if jlpt == 4:
        return 2
    if jlpt == 3:
        return 3
    if jlpt == 2:
        return 4
    if jlpt == 1:
        return 5

    if grade is not None:
        if grade <= 1:
            return 1
        if grade <= 3:
            return 2
        if grade <= 5:
            return 3
        if grade <= 8:
            return 4

    if stroke_count is not None:
        if stroke_count <= 5:
            return 1
        if stroke_count <= 8:
            return 2
        if stroke_count <= 12:
            return 3
        if stroke_count <= 16:
            return 4

    return 5
