from app.services.kanji_power import calculate_kanji_power


def test_kanji_power_prefers_jlpt_metadata() -> None:
    assert calculate_kanji_power(jlpt=5, grade=8, stroke_count=20) == 1
    assert calculate_kanji_power(jlpt=1, grade=1, stroke_count=1) == 5


def test_kanji_power_falls_back_to_grade_and_strokes() -> None:
    assert calculate_kanji_power(jlpt=None, grade=1, stroke_count=20) == 1
    assert calculate_kanji_power(jlpt=None, grade=None, stroke_count=17) == 5
