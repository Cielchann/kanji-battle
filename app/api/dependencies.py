from app.repositories.battle_repo import BattleRepository
from app.repositories.kanji_repo import KanjiRepository
from app.repositories.leaderboard_repo import LeaderboardRepository
from app.repositories.progress_repo import ProgressRepository
from app.repositories.question_repo import QuestionRepository
from app.repositories.shop_repo import ShopRepository
from app.services.kanji_api import KanjiApiClient

question_repository = QuestionRepository()
battle_repository = BattleRepository(question_repository)
leaderboard_repository = LeaderboardRepository()
progress_repository = ProgressRepository()
kanji_repository = KanjiRepository()
kanji_api_client = KanjiApiClient()
shop_repository = ShopRepository()


def get_question_repository() -> QuestionRepository:
    return question_repository


def get_battle_repository() -> BattleRepository:
    return battle_repository


def get_leaderboard_repository() -> LeaderboardRepository:
    return leaderboard_repository


def get_progress_repository() -> ProgressRepository:
    return progress_repository


def get_kanji_repository() -> KanjiRepository:
    return kanji_repository


def get_kanji_api_client() -> KanjiApiClient:
    return kanji_api_client


def get_shop_repository() -> ShopRepository:
    return shop_repository
