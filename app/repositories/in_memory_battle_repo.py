from app.services.battle_engine import BattleSession


class InMemoryBattleRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, BattleSession] = {}

    def save(self, session: BattleSession) -> BattleSession:
        self._sessions[session.battle_id] = session
        return session

    def get(self, battle_id: str) -> BattleSession | None:
        return self._sessions.get(battle_id)

