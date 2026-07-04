# JLPT Kanji Battle Online

JLPT Kanji Battle Online is a portfolio-grade educational web game for practicing JLPT kanji and vocabulary through a simple battle system.

Players answer kanji or vocabulary questions to attack a monster. Correct answers deal damage and increase combo. Wrong answers make the player take damage and reset combo.

## Portfolio Goal

This project is designed to demonstrate:

- Python backend development
- API design with FastAPI
- Web application logic
- Database-ready domain modeling
- Testable game rules
- Interest in Japanese learning and JLPT

## MVP Scope

- Single-player battle mode
- Random N5-N1 question pool by default
- Difficulty-based weighted N5-N1 question mix
- Difficulty selection: easy, medium, hard, extreme, hell
- Difficulty unlock rules for Extreme and Hell
- English and Japanese question display
- Question answering flow
- Player HP, monster HP, score, and combo
- Question power affects both attack damage and wrong-answer damage
- Clear rewards: score, XP, and gold
- Win/loss battle result
- Online-ready weekly leaderboard with player names
- Seed questions for initial development

## Planned Stack

- Backend: FastAPI
- Runtime server: Uvicorn
- Database: SQLite locally, PostgreSQL online
- ORM: SQLAlchemy
- Migration: Alembic
- Testing: pytest
- Deployment: Render or Railway

## Development Status

Current phase: playable FastAPI + Phaser MVP with SQLite local support and Neon PostgreSQL online support.

## Local Run

Create and activate a virtual environment, then install the project:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Run tests:

```powershell
.\.venv\Scripts\python -m pytest
```

Create a local `.env` file for online database testing. This file is ignored by git:

```text
DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
AUTO_CREATE_TABLES="false"
```

Run the API server:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Production start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Online Database

The app is PostgreSQL-ready. Set `DATABASE_URL` to an online PostgreSQL connection string:

```text
DATABASE_URL="postgresql+psycopg://user:password@host:5432/dbname"
```

Common hosted providers may give `postgres://...` or `postgresql://...`; the app normalizes both to the `psycopg` driver internally.

Run migrations:

```powershell
.\.venv\Scripts\python -m alembic upgrade head
```

Sync local starter kanji/questions into the configured online database:

```powershell
.\.venv\Scripts\python scripts\sync_sqlite_seed_to_database.py
```

If the hosted PostgreSQL connection is unstable, use the raw psycopg sync helper:

```powershell
.\.venv\Scripts\python scripts\sync_sqlite_to_postgres_raw.py
```

For production-style deployment, set:

```text
AUTO_CREATE_TABLES="false"
```

For local PostgreSQL testing:

```powershell
docker compose up -d postgres
```

Then use:

```text
DATABASE_URL="postgresql+psycopg://jlpt:jlpt_dev_password@localhost:5432/jlpt_kanji_battle"
```

## Battle Options

Start a mixed N5-N1 battle:

```json
{
  "player_name": "Afras",
  "device_token": "device-local-random-token",
  "difficulty": "easy",
  "language": "en"
}
```

Start a harder mixed battle in Japanese:

```json
{
  "player_name": "Afras",
  "device_token": "device-local-random-token",
  "difficulty": "hell",
  "language": "ja"
}
```

The player does not choose a JLPT level. The selected difficulty controls the question mix:

- `easy`: mostly N5, some N4
- `medium`: mostly N4, with N5 and N3
- `hard`: mostly N3, with N4 and N2
- `extreme`: mostly N2, with N3 and N1
- `hell`: mostly N1, with some N2

## Difficulty Unlock Rules

The first three difficulties are open by default:

- `easy`
- `medium`
- `hard`

Advanced difficulties require perfect clears:

- `extreme`: unlocks after 2 perfect clears on `hard`
- `hell`: unlocks after 1 perfect clear on each of `easy`, `medium`, `hard`, and `extreme`

A perfect clear means winning the battle while player HP is still full.

## Rewards

Clearing a battle grants score, XP, and gold. Perfect clears grant bonus XP and gold.

Question power is currently derived from the question's JLPT metadata:

- N5: Power 1
- N4: Power 2
- N3: Power 3
- N2: Power 4
- N1: Power 5

Higher power questions deal more damage when answered correctly, but also make the player take more damage when answered incorrectly.

Monster HP is scaled by difficulty:

- `easy`: 100,000 HP
- `medium`: 250,000 HP
- `hard`: 600,000 HP
- `extreme`: 1,200,000 HP
- `hell`: 2,400,000 HP

Player starting HP uses the same difficulty scale. Wrong-answer damage is also scaled by difficulty and kanji power, so harder kanji create higher risk and higher reward.

Damage is balanced around roughly 10 correct answers per clear, with question power and combo modifying the exact amount.

Current reward base:

- `easy`: 20 XP, 10 gold
- `medium`: 40 XP, 20 gold
- `hard`: 70 XP, 35 gold
- `extreme`: 120 XP, 60 gold
- `hell`: 200 XP, 100 gold

The player profile can be checked with:

```text
GET /players/{player_name}/progress?device_token=device-local-random-token
```

## Leaderboard

Finished battles are saved to `scores` and can be ranked by score and max combo:

```text
GET /leaderboard
GET /leaderboard?difficulty=hell
GET /leaderboard?current_week_only=false
```

By default, leaderboard results are limited to the current week. This behaves like a weekly reset without deleting historical score data.

The leaderboard shows each player once per difficulty/week using that player's best score. Full score history can still remain in the database.

For the current MVP, a player name is claimed by the first browser/device token that uses it. Another device cannot reuse the same name. Later, this can be replaced by authenticated user accounts.

## Database

Local development uses SQLite by default:

```text
sqlite:///./jlpt_battle.db
```

The app creates tables and seeds initial questions on startup. The same repository structure is intended to support PostgreSQL later by changing `DATABASE_URL`.

Current tables:

- `kanji_entries`
- `questions`
- `battle_sessions`
- `battle_turns`
- `scores`
- `player_profiles`
- `difficulty_progress`
- `weapons`
- `player_weapons`

## Kanji API Cache

Kanji data is fetched server-side from KanjiAPI.dev and cached in the local database.

The frontend does not call external APIs directly. This keeps external API URLs, future API keys, and import logic inside the backend.

Lookup and cache one kanji:

```text
GET /kanji/山
```

Import a small batch:

```text
POST /kanji/import
```

```json
{
  "characters": ["山", "水", "火"],
  "refresh": false
}
```

If `ADMIN_IMPORT_TOKEN` is configured, import requests must include the `X-Admin-Token` header.

Import the starter pack:

```text
POST /kanji/import/starter
```

Or run it server-side:

```powershell
.\.venv\Scripts\python scripts\import_starter_kanji.py
```

Import the full JLPT kanji cache from KanjiAPI.dev and generate battle questions:

```powershell
.\.venv\Scripts\python scripts\import_jlpt_kanji.py --levels 5 4 3 2 1 --workers 8
```

The starter pack contains common beginner-friendly kanji and is cached server-side before battle questions are generated.

## Weapon Shop

Players earn gold from clear rewards and can buy/equip weapons:

```text
GET /shop/weapons?player_name=Afras&device_token=device-local-random-token
POST /shop/buy
POST /shop/equip
```

Weapons add an attack bonus to battle damage. The starter weapon is granted automatically.
