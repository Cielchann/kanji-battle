import random

from app.models.enums import Difficulty, JlptLevel, QuestionType
from app.schemas.kanji import KanjiEntry
from app.schemas.question import LocalizedQuestionContent, Question


POWER_TO_DIFFICULTY: dict[int, Difficulty] = {
    1: Difficulty.EASY,
    2: Difficulty.MEDIUM,
    3: Difficulty.HARD,
    4: Difficulty.EXTREME,
    5: Difficulty.HELL,
}

JLPT_NUMBER_TO_LEVEL: dict[int, JlptLevel] = {
    5: JlptLevel.N5,
    4: JlptLevel.N4,
    3: JlptLevel.N3,
    2: JlptLevel.N2,
    1: JlptLevel.N1,
}

POWER_TO_FALLBACK_LEVEL: dict[int, JlptLevel] = {
    1: JlptLevel.N5,
    2: JlptLevel.N4,
    3: JlptLevel.N3,
    4: JlptLevel.N2,
    5: JlptLevel.N1,
}

KANJI_QUESTION_ID_OFFSET = 1_000_000

COMMON_READING_OVERRIDES: dict[str, str] = {
    "日": "ひ",
    "月": "つき",
    "火": "ひ",
    "水": "みず",
    "木": "き",
    "金": "かね",
    "土": "つち",
    "山": "やま",
    "川": "かわ",
    "田": "た",
    "人": "ひと",
    "口": "くち",
    "目": "め",
    "耳": "みみ",
    "手": "て",
    "足": "あし",
    "力": "ちから",
    "女": "おんな",
    "男": "おとこ",
    "子": "こ",
    "父": "ちち",
    "母": "はは",
    "友": "とも",
    "先": "さき",
    "生": "せい",
    "学": "がく",
    "校": "こう",
    "年": "とし",
    "時": "とき",
    "分": "ふん",
    "半": "はん",
    "上": "うえ",
    "下": "した",
    "中": "なか",
    "外": "そと",
    "右": "みぎ",
    "左": "ひだり",
    "前": "まえ",
    "後": "うしろ",
    "東": "ひがし",
    "西": "にし",
    "南": "みなみ",
    "北": "きた",
    "大": "おおきい",
    "小": "ちいさい",
    "高": "たかい",
    "安": "やすい",
    "新": "あたらしい",
    "古": "ふるい",
    "長": "ながい",
    "白": "しろ",
    "黒": "くろ",
    "赤": "あか",
    "青": "あお",
    "円": "えん",
    "百": "ひゃく",
    "千": "せん",
    "万": "まん",
    "一": "いち",
    "二": "に",
    "三": "さん",
    "四": "よん",
    "五": "ご",
    "六": "ろく",
    "七": "なな",
    "八": "はち",
    "九": "きゅう",
    "十": "じゅう",
    "本": "ほん",
    "語": "ご",
    "車": "くるま",
    "電": "でん",
    "駅": "えき",
    "会": "かい",
    "社": "しゃ",
    "店": "みせ",
    "買": "かう",
    "行": "いく",
    "来": "くる",
    "見": "みる",
    "聞": "きく",
    "話": "はなす",
    "読": "よむ",
    "書": "かく",
    "食": "たべる",
    "飲": "のむ",
    "休": "やすむ",
    "何": "なに",
    "名": "な",
    "毎": "まい",
    "気": "き",
    "天": "てん",
    "雨": "あめ",
    "空": "そら",
    "花": "はな",
    "魚": "さかな",
    "犬": "いぬ",
    "鳥": "とり",
    "道": "みち",
    "国": "くに",
}


def _primary_reading(entry: KanjiEntry) -> str | None:
    if entry.character in COMMON_READING_OVERRIDES:
        return COMMON_READING_OVERRIDES[entry.character]

    readings = entry.kun_readings or entry.on_readings
    if not readings:
        return None
    candidate_readings = [reading for reading in readings if "-" not in reading]
    standalone_readings = [reading for reading in candidate_readings if "." not in reading]
    selected_reading = (
        standalone_readings[0]
        if standalone_readings
        else candidate_readings[0]
        if candidate_readings
        else readings[0]
    )
    return _normalize_reading(selected_reading)


def _primary_meaning(entry: KanjiEntry) -> str | None:
    if not entry.meanings:
        return None
    return entry.meanings[0]


def _question_id(character: str, question_type_index: int) -> int:
    return KANJI_QUESTION_ID_OFFSET + (ord(character) * 10) + question_type_index


def _choices(
    correct_answer: str,
    distractor_groups: list[list[str]],
    seed: str,
    clean_reading: bool,
) -> list[str]:
    seen = {correct_answer}
    choices = [correct_answer]

    for index, group in enumerate(distractor_groups):
        for distractor in _shuffled_unique(group, f"{seed}:{index}", clean_reading=clean_reading):
            if distractor and distractor not in seen:
                seen.add(distractor)
                choices.append(distractor)
            if len(choices) == 4:
                return choices
    return choices


def _shuffled_unique(values: list[str], seed: str, clean_reading: bool) -> list[str]:
    normalized_values = _clean_readings(values) if clean_reading else _clean_options(values)
    unique_values = list(dict.fromkeys(normalized_values))
    rng = random.Random(seed)
    rng.shuffle(unique_values)
    return unique_values


def _reading_script(reading: str) -> str:
    if any("\u30a0" <= character <= "\u30ff" for character in reading):
        return "katakana"
    return "hiragana"


def _entry_readings(entry: KanjiEntry) -> list[str]:
    source_readings = [
        reading
        for reading in [*entry.kun_readings, *entry.on_readings]
        if "-" not in reading
    ]
    readings = _clean_readings(source_readings)
    if entry.character in COMMON_READING_OVERRIDES:
        readings.insert(0, COMMON_READING_OVERRIDES[entry.character])
    return readings


def _reading_distractor_groups(entry: KanjiEntry, entries: list[KanjiEntry], correct_answer: str) -> list[list[str]]:
    target_script = _reading_script(correct_answer)
    needs_longer_distractor = len(correct_answer) >= 2
    same_power_entries = [
        other for other in entries if other.character != entry.character and other.power == entry.power
    ]
    adjacent_power_entries = [
        other
        for other in entries
        if other.character != entry.character and abs(other.power - entry.power) <= 1
    ]

    same_power_readings = [
        reading for other in same_power_entries for reading in _entry_readings(other)
    ]
    adjacent_power_readings = [
        reading for other in adjacent_power_entries for reading in _entry_readings(other)
    ]
    same_power_primary_readings = [
        reading
        for other in same_power_entries
        if (reading := _primary_reading(other)) is not None
    ]
    adjacent_power_primary_readings = [
        reading
        for other in adjacent_power_entries
        if (reading := _primary_reading(other)) is not None
    ]
    all_readings = [
        reading for other in entries if other.character != entry.character for reading in _entry_readings(other)
    ]

    def same_script(reading: str) -> bool:
        return _reading_script(reading) == target_script

    def similar_length(reading: str) -> bool:
        return not needs_longer_distractor or len(reading) >= 2

    return [
        [reading for reading in same_power_primary_readings if same_script(reading) and similar_length(reading)],
        [reading for reading in adjacent_power_primary_readings if same_script(reading) and similar_length(reading)],
        [reading for reading in same_power_readings if same_script(reading) and similar_length(reading)],
        [reading for reading in adjacent_power_readings if same_script(reading) and similar_length(reading)],
        [reading for reading in same_power_readings if same_script(reading)],
        [reading for reading in adjacent_power_readings if same_script(reading)],
        same_power_readings,
        all_readings,
    ]


def _meaning_distractor_groups(entry: KanjiEntry, entries: list[KanjiEntry]) -> list[list[str]]:
    same_power_entries = [
        other for other in entries if other.character != entry.character and other.power == entry.power
    ]
    adjacent_power_entries = [
        other
        for other in entries
        if other.character != entry.character and abs(other.power - entry.power) <= 1
    ]
    return [
        [meaning for other in same_power_entries for meaning in other.meanings],
        [meaning for other in adjacent_power_entries for meaning in other.meanings],
        [meaning for other in entries if other.character != entry.character for meaning in other.meanings],
    ]


def generate_questions_from_kanji(entries: list[KanjiEntry]) -> list[Question]:
    questions: list[Question] = []
    for entry in entries:
        jlpt_level = (
            JLPT_NUMBER_TO_LEVEL.get(entry.jlpt)
            if entry.jlpt is not None
            else None
        ) or POWER_TO_FALLBACK_LEVEL[entry.power]
        difficulty = POWER_TO_DIFFICULTY[entry.power]
        reading = _primary_reading(entry)
        meaning = _primary_meaning(entry)

        if reading is not None:
            choices = _choices(
                reading,
                _reading_distractor_groups(entry, entries, reading),
                seed=f"reading:{entry.character}:{reading}",
                clean_reading=True,
            )
            if len(choices) >= 2:
                questions.append(
                    Question(
                        id=_question_id(entry.character, 1),
                        jlpt_level=jlpt_level,
                        difficulty=difficulty,
                        question_type=QuestionType.KANJI_READING,
                        prompt=entry.character,
                        content_en=LocalizedQuestionContent(
                            question_text="Choose the correct reading.",
                            choices=choices,
                            correct_answer=reading,
                            explanation=f"{entry.character} is read as {reading}.",
                        ),
                        content_ja=LocalizedQuestionContent(
                            question_text="正しい読み方を選んでください。",
                            choices=choices,
                            correct_answer=reading,
                            explanation=f"{entry.character}の読み方は「{reading}」です。",
                        ),
                    )
                )

        if meaning is not None:
            choices = _choices(
                meaning,
                _meaning_distractor_groups(entry, entries),
                seed=f"meaning:{entry.character}:{meaning}",
                clean_reading=False,
            )
            if len(choices) >= 2:
                questions.append(
                    Question(
                        id=_question_id(entry.character, 2),
                        jlpt_level=jlpt_level,
                        difficulty=difficulty,
                        question_type=QuestionType.VOCAB_MEANING,
                        prompt=entry.character,
                        content_en=LocalizedQuestionContent(
                            question_text="Choose the correct meaning.",
                            choices=choices,
                            correct_answer=meaning,
                            explanation=f"{entry.character} means {meaning}.",
                        ),
                        content_ja=LocalizedQuestionContent(
                            question_text="正しい意味を選んでください。",
                            choices=choices,
                            correct_answer=meaning,
                            explanation=f"{entry.character}は英語で {meaning} です。",
                        ),
                    )
                )

    return questions


def _clean_readings(readings: list[str]) -> list[str]:
    return [_normalize_reading(reading) for reading in readings if reading]


def _normalize_reading(reading: str) -> str:
    return reading.replace("-", "").replace(".", "").strip()


def _clean_options(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value and value.strip()]
