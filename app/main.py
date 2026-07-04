from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import battle, health, kanji, leaderboard, players, questions, shop
from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.session import SessionLocal, create_db_and_tables
from app.repositories.question_repo import QuestionRepository
from app.repositories.shop_repo import ShopRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    if get_settings().auto_create_tables:
        create_db_and_tables()
        with SessionLocal() as db:
            QuestionRepository().seed_initial_questions(db)
            ShopRepository().seed_weapons(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="JLPT Kanji Battle Online API",
        version="0.1.0",
        description="Backend API for a JLPT kanji and vocabulary battle game.",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(questions.router, prefix="/questions", tags=["questions"])
    app.include_router(battle.router, prefix="/battle", tags=["battle"])
    app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
    app.include_router(players.router, prefix="/players", tags=["players"])
    app.include_router(kanji.router, prefix="/kanji", tags=["kanji"])
    app.include_router(shop.router, prefix="/shop", tags=["shop"])

    web_dir = Path(__file__).resolve().parent.parent / "web"
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/", include_in_schema=False)
    def game_page() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    return app


app = create_app()
