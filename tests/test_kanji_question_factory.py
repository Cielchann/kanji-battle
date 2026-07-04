from app.schemas.kanji import KanjiEntry
from app.services.kanji_question_factory import generate_questions_from_kanji


def test_generate_questions_from_cached_kanji() -> None:
    entries = [
        KanjiEntry(
            character="山",
            meanings=["mountain"],
            kun_readings=["やま"],
            on_readings=["サン"],
            name_readings=[],
            stroke_count=3,
            grade=1,
            jlpt=5,
            unicode="5C71",
            power=1,
        ),
        KanjiEntry(
            character="水",
            meanings=["water"],
            kun_readings=["みず"],
            on_readings=["スイ"],
            name_readings=[],
            stroke_count=4,
            grade=1,
            jlpt=5,
            unicode="6C34",
            power=1,
        ),
    ]

    questions = generate_questions_from_kanji(entries)

    assert len(questions) == 4
    assert {question.prompt for question in questions} == {"山", "水"}
    assert all(len(question.content_en.choices) >= 2 for question in questions)


def test_generated_reading_distractors_vary_by_kanji() -> None:
    entries = [
        KanjiEntry(
            character="一",
            meanings=["one"],
            kun_readings=["ひと"],
            on_readings=["イチ"],
            stroke_count=1,
            grade=1,
            jlpt=5,
            unicode="4E00",
            power=1,
        ),
        KanjiEntry(
            character="風",
            meanings=["wind"],
            kun_readings=["かぜ"],
            on_readings=["フウ"],
            stroke_count=9,
            grade=2,
            jlpt=4,
            unicode="98A8",
            power=2,
        ),
        KanjiEntry(
            character="雨",
            meanings=["rain"],
            kun_readings=["あめ"],
            on_readings=["ウ"],
            stroke_count=8,
            grade=1,
            jlpt=5,
            unicode="96E8",
            power=1,
        ),
        KanjiEntry(
            character="花",
            meanings=["flower"],
            kun_readings=["はな"],
            on_readings=["カ"],
            stroke_count=7,
            grade=1,
            jlpt=5,
            unicode="82B1",
            power=1,
        ),
        KanjiEntry(
            character="空",
            meanings=["sky"],
            kun_readings=["そら"],
            on_readings=["クウ"],
            stroke_count=8,
            grade=1,
            jlpt=5,
            unicode="7A7A",
            power=1,
        ),
    ]

    questions = generate_questions_from_kanji(entries)
    reading_choices = {
        question.prompt: question.content_ja.choices
        for question in questions
        if question.question_type == "kanji_reading"
    }

    assert reading_choices["風"] != ["かぜ", "ひと", "ひとつ", "イチ"]
    assert len({tuple(choices) for choices in reading_choices.values()}) > 1
