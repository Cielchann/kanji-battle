from dataclasses import dataclass, field
from uuid import uuid4

from app.models.enums import BattleStatus, Difficulty, DisplayLanguage, JlptLevel
from app.schemas.battle import BattleState, Monster
from app.schemas.question import (
    QUESTION_POWER_BY_JLPT_LEVEL,
    Question,
    get_localized_content,
    to_public_question,
)
from app.services.battle_balance import MONSTER_HP_BY_DIFFICULTY, PLAYER_HP_BY_DIFFICULTY
from app.services.question_selector import QuestionSelector
from app.services.rewards import calculate_clear_reward
from app.services.scoring import (
    calculate_damage,
    calculate_score_gain,
    calculate_wrong_answer_damage,
)


@dataclass
class BattleSession:
    battle_id: str
    player_name: str
    jlpt_level: JlptLevel | None
    difficulty: Difficulty
    language: DisplayLanguage
    player_hp: int
    monster_name: str
    monster_max_hp: int
    monster_hp: int
    weapon_name: str | None = None
    weapon_attack_bonus: int = 0
    combo: int = 0
    max_combo: int = 0
    score: int = 0
    xp_earned: int = 0
    gold_earned: int = 0
    turn: int = 1
    status: BattleStatus = BattleStatus.IN_PROGRESS
    current_question: Question | None = None
    used_question_ids: set[int] = field(default_factory=set)


class BattleEngine:
    def __init__(self, question_selector: QuestionSelector) -> None:
        self._question_selector = question_selector

    def start(
        self,
        player_name: str,
        jlpt_level: JlptLevel | None,
        difficulty: Difficulty,
        language: DisplayLanguage,
        weapon_name: str | None = None,
        weapon_attack_bonus: int = 0,
    ) -> BattleSession:
        monster_hp = MONSTER_HP_BY_DIFFICULTY[difficulty]
        player_hp = PLAYER_HP_BY_DIFFICULTY[difficulty]
        level_label = jlpt_level if jlpt_level is not None else "N5-N1"
        session = BattleSession(
            battle_id=str(uuid4()),
            player_name=player_name.strip() or "Guest Player",
            jlpt_level=jlpt_level,
            difficulty=difficulty,
            language=language,
            player_hp=player_hp,
            monster_name=f"{level_label} {difficulty.value.title()} Kanji Oni",
            monster_max_hp=monster_hp,
            monster_hp=monster_hp,
            weapon_name=weapon_name,
            weapon_attack_bonus=weapon_attack_bonus,
        )
        session.current_question = self._question_selector.next_question(
            jlpt_level,
            difficulty,
            set(),
            language,
        )
        session.used_question_ids.add(session.current_question.id)
        return session

    def answer(self, session: BattleSession, question_id: int, answer: str) -> tuple[bool, int, int, str | None]:
        if session.status != BattleStatus.IN_PROGRESS:
            return False, 0, 0, None

        if session.current_question is None or session.current_question.id != question_id:
            msg = "Question does not match the current battle turn."
            raise ValueError(msg)

        normalized_answer = answer.strip()
        current_content = get_localized_content(session.current_question, session.language)
        question_power = QUESTION_POWER_BY_JLPT_LEVEL[session.current_question.jlpt_level]
        is_correct = normalized_answer == current_content.correct_answer
        damage_dealt = 0
        damage_taken = 0
        explanation = current_content.explanation

        if is_correct:
            damage_dealt = calculate_damage(
                session.monster_max_hp,
                session.combo,
                question_power,
                session.weapon_attack_bonus,
            )
            session.monster_hp = max(0, session.monster_hp - damage_dealt)
            session.score += calculate_score_gain(session.combo, question_power)
            session.combo += 1
            session.max_combo = max(session.max_combo, session.combo)
        else:
            damage_taken = calculate_wrong_answer_damage(
                PLAYER_HP_BY_DIFFICULTY[session.difficulty],
                question_power,
            )
            session.player_hp = max(0, session.player_hp - damage_taken)
            session.combo = 0

        if session.monster_hp == 0:
            session.status = BattleStatus.WON
            reward = calculate_clear_reward(
                session.difficulty,
                is_perfect_clear=session.player_hp == PLAYER_HP_BY_DIFFICULTY[session.difficulty],
            )
            session.xp_earned = reward.xp
            session.gold_earned = reward.gold
            session.current_question = None
        elif session.player_hp == 0:
            session.status = BattleStatus.LOST
            session.current_question = None
        else:
            session.turn += 1
            session.current_question = self._question_selector.next_question(
                session.jlpt_level,
                session.difficulty,
                session.used_question_ids,
                session.language,
            )
            session.used_question_ids.add(session.current_question.id)

        return is_correct, damage_dealt, damage_taken, explanation


def to_battle_state(session: BattleSession) -> BattleState:
    public_question = (
        to_public_question(session.current_question, session.language)
        if session.current_question is not None
        else None
    )
    return BattleState(
        battle_id=session.battle_id,
        player_name=session.player_name,
        jlpt_level=session.jlpt_level,
        difficulty=session.difficulty,
        language=session.language,
        player_hp=session.player_hp,
        monster=Monster(
            name=session.monster_name,
            max_hp=session.monster_max_hp,
            hp=session.monster_hp,
        ),
        weapon_name=session.weapon_name,
        weapon_attack_bonus=session.weapon_attack_bonus,
        combo=session.combo,
        score=session.score,
        xp_earned=session.xp_earned,
        gold_earned=session.gold_earned,
        turn=session.turn,
        status=session.status,
        current_question=public_question,
    )
