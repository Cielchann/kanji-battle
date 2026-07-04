from fastapi.testclient import TestClient
import pytest
from uuid import uuid4

from app.main import app
from app.db.models import ScoreRecord, current_week_start
from app.db.session import SessionLocal
from app.models.enums import Difficulty
from app.repositories.question_repo import QuestionRepository
from app.schemas.question import get_localized_content
from app.services.battle_balance import PLAYER_HP_BY_DIFFICULTY


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def correct_answer(question: dict, language: str = "en") -> str:
    with SessionLocal() as db:
        stored_question = QuestionRepository().get(db, question["id"])
        assert stored_question is not None
        return get_localized_content(stored_question, language).correct_answer


def device_token(player_name: str) -> str:
    return f"test-device-token-{player_name}"


def test_battle_start_and_answer_flow(client) -> None:
    player_name = f"FLOW-{uuid4().hex[:8]}"
    start_response = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "easy",
            "language": "en",
        },
    )

    assert start_response.status_code == 200
    state = start_response.json()
    question = state["current_question"]
    assert state["player_name"] == player_name

    answer_response = client.post(
        "/battle/answer",
        json={
            "battle_id": state["battle_id"],
            "question_id": question["id"],
            "answer": correct_answer(question),
        },
    )

    assert answer_response.status_code == 200
    payload = answer_response.json()
    assert "is_correct" in payload
    assert "state" in payload


def test_questions_can_be_returned_in_japanese(client) -> None:
    response = client.get("/questions", params={"difficulty": "hell", "language": "ja"})

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["language"] == "ja"
    assert "question_text" in payload[0]
    assert all(question["question_type"] == "kanji_reading" for question in payload)


def test_japanese_battle_uses_reading_questions(client) -> None:
    player_name = f"JA-{uuid4().hex[:8]}"
    start_response = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "easy",
            "language": "ja",
        },
    )

    assert start_response.status_code == 200
    question = start_response.json()["current_question"]
    assert question["language"] == "ja"
    assert question["question_type"] == "kanji_reading"


def test_finished_battle_is_saved_to_leaderboard(client) -> None:
    player_name = f"LB-{uuid4().hex[:8]}"
    start_response = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "easy",
            "language": "en",
        },
    )
    assert start_response.status_code == 200

    state = start_response.json()
    for _ in range(30):
        question = state["current_question"]
        if question is None:
            break
        answer_response = client.post(
            "/battle/answer",
            json={
                "battle_id": state["battle_id"],
                "question_id": question["id"],
                "answer": correct_answer(question),
            },
        )
        assert answer_response.status_code == 200
        state = answer_response.json()["state"]
        if state["status"] != "in_progress":
            break

    assert state["status"] == "won"

    leaderboard_response = client.get(
        "/leaderboard",
        params={"difficulty": "easy", "limit": 100},
    )

    assert leaderboard_response.status_code == 200
    leaderboard = leaderboard_response.json()
    assert leaderboard
    matching_entries = [
        entry for entry in leaderboard if entry["player_name"] == player_name
    ]
    assert matching_entries
    assert matching_entries[0]["score"] > 0
    assert matching_entries[0]["xp_earned"] > 0
    assert matching_entries[0]["gold_earned"] > 0


def complete_perfect_battle(client, player_name: str, difficulty: str) -> dict:
    start_response = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": difficulty,
            "language": "en",
        },
    )
    assert start_response.status_code == 200

    state = start_response.json()
    for _ in range(30):
        question = state["current_question"]
        if question is None:
            break
        answer_response = client.post(
            "/battle/answer",
            json={
                "battle_id": state["battle_id"],
                "question_id": question["id"],
                "answer": correct_answer(question),
            },
        )
        assert answer_response.status_code == 200
        state = answer_response.json()["state"]
        if state["status"] != "in_progress":
            break

    assert state["status"] == "won"
    assert state["player_hp"] == PLAYER_HP_BY_DIFFICULTY[Difficulty(difficulty)]
    assert state["xp_earned"] > 0
    assert state["gold_earned"] > 0
    return state


def test_extreme_and_hell_unlock_require_perfect_clears(client) -> None:
    player_name = f"UL-{uuid4().hex[:8]}"

    locked_extreme = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "extreme",
            "language": "en",
        },
    )
    assert locked_extreme.status_code == 403

    complete_perfect_battle(client, player_name, "hard")

    still_locked_extreme = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "extreme",
            "language": "en",
        },
    )
    assert still_locked_extreme.status_code == 403

    complete_perfect_battle(client, player_name, "hard")

    unlocked_extreme = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "extreme",
            "language": "en",
        },
    )
    assert unlocked_extreme.status_code == 200

    locked_hell = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "hell",
            "language": "en",
        },
    )
    assert locked_hell.status_code == 403

    complete_perfect_battle(client, player_name, "easy")
    complete_perfect_battle(client, player_name, "medium")
    complete_perfect_battle(client, player_name, "extreme")

    unlocked_hell = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "hell",
            "language": "en",
        },
    )
    assert unlocked_hell.status_code == 200

    progress_response = client.get(
        f"/players/{player_name}/progress",
        params={"device_token": device_token(player_name)},
    )
    assert progress_response.status_code == 200
    progress = progress_response.json()
    assert progress["xp"] > 0
    assert progress["gold"] > 0
    assert all(item["unlocked"] for item in progress["difficulties"])


def test_shop_lists_and_equips_starter_weapon(client) -> None:
    player_name = f"SHOP-{uuid4().hex[:8]}"

    weapons_response = client.get(
        "/shop/weapons",
        params={
            "player_name": player_name,
            "device_token": device_token(player_name),
        },
    )
    assert weapons_response.status_code == 200
    weapons = weapons_response.json()
    starter = next(weapon for weapon in weapons if weapon["id"] == "wooden_tanto")
    assert starter["owned"] is True

    equip_response = client.post(
        "/shop/equip",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "weapon_id": "wooden_tanto",
        },
    )
    assert equip_response.status_code == 200

    start_response = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": device_token(player_name),
            "difficulty": "easy",
            "language": "en",
        },
    )
    assert start_response.status_code == 200
    battle = start_response.json()
    assert battle["weapon_name"] == "Wooden Tanto"
    assert battle["weapon_attack_bonus"] == 0


def test_player_name_is_locked_to_first_device(client) -> None:
    player_name = f"LOCK-{uuid4().hex[:8]}"
    first_token = device_token(player_name)
    other_token = f"other-device-token-{uuid4().hex[:8]}"

    first_response = client.get(
        f"/players/{player_name}/progress",
        params={"device_token": first_token},
    )
    assert first_response.status_code == 200

    same_device_response = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": first_token,
            "difficulty": "easy",
            "language": "en",
        },
    )
    assert same_device_response.status_code == 200

    other_device_progress = client.get(
        f"/players/{player_name}/progress",
        params={"device_token": other_token},
    )
    assert other_device_progress.status_code == 409

    other_device_start = client.post(
        "/battle/start",
        json={
            "player_name": player_name,
            "device_token": other_token,
            "difficulty": "easy",
            "language": "en",
        },
    )
    assert other_device_start.status_code == 409


def test_leaderboard_returns_every_score_for_same_player(client) -> None:
    player_name = f"RUNS-{uuid4().hex[:8]}"
    with SessionLocal() as db:
        db.add_all(
            [
                ScoreRecord(
                    battle_id=f"score-low-{uuid4()}",
                    player_name=player_name,
                    jlpt_level=None,
                    difficulty="easy",
                    score=900,
                    max_combo=3,
                    xp_earned=10,
                    gold_earned=5,
                    status="won",
                    week_start=current_week_start(),
                ),
                ScoreRecord(
                    battle_id=f"score-high-{uuid4()}",
                    player_name=player_name,
                    jlpt_level=None,
                    difficulty="easy",
                    score=2000,
                    max_combo=8,
                    xp_earned=20,
                    gold_earned=10,
                    status="won",
                    week_start=current_week_start(),
                ),
            ]
        )
        db.commit()

    leaderboard_response = client.get(
        "/leaderboard",
        params={"difficulty": "easy", "limit": 100},
    )
    assert leaderboard_response.status_code == 200
    leaderboard = leaderboard_response.json()
    matches = [entry for entry in leaderboard if entry["player_name"] == player_name]
    assert len(matches) == 2
    assert [entry["score"] for entry in matches] == [2000, 900]
