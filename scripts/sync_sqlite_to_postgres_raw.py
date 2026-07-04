from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from time import sleep

import psycopg

from app.core.config import get_settings
from app.db.url import normalize_database_url


ROOT_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = ROOT_DIR / "jlpt_battle.db"


def connect_with_retry() -> psycopg.Connection:
    dsn = normalize_database_url(get_settings().database_url).replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )
    last_error: Exception | None = None
    for attempt in range(1, 11):
        print(f"connect_attempt={attempt}", flush=True)
        try:
            return psycopg.connect(dsn, connect_timeout=8)
        except psycopg.OperationalError as exc:
            last_error = exc
            sleep(min(attempt * 2, 10))
    if last_error is None:
        raise RuntimeError("Database connection failed.")
    raise last_error


def json_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def ensure_online_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "alter table player_profiles "
            "add column if not exists owner_token varchar(128)"
        )
        cur.execute(
            "create index if not exists ix_player_profiles_owner_token "
            "on player_profiles(owner_token)"
        )
        cur.execute("select count(*) from alembic_version")
        has_revision = cur.fetchone()[0] > 0
        if has_revision:
            cur.execute(
                "update alembic_version set version_num = %s",
                ("0002_player_owner_token",),
            )
        else:
            cur.execute(
                "insert into alembic_version(version_num) values (%s)",
                ("0002_player_owner_token",),
            )
    conn.commit()


def sync_kanji(source: sqlite3.Connection, target: psycopg.Connection) -> int:
    rows = source.execute(
        "select character, meanings, kun_readings, on_readings, name_readings, "
        "stroke_count, grade, jlpt, unicode, power, source, cached_at "
        "from kanji_entries"
    ).fetchall()
    columns = (
        "character, meanings, kun_readings, on_readings, name_readings, "
        "stroke_count, grade, jlpt, unicode, power, source, cached_at"
    )
    with target.cursor() as cur:
        cur.execute(
            """
            create temporary table tmp_kanji_entries(
                character varchar(8),
                meanings json,
                kun_readings json,
                on_readings json,
                name_readings json,
                stroke_count integer,
                grade integer,
                jlpt integer,
                unicode varchar(20),
                power integer,
                source varchar(80),
                cached_at timestamptz
            ) on commit drop
            """
        )
        with cur.copy(f"copy tmp_kanji_entries({columns}) from stdin") as copy:
            for row in rows:
                copy.write_row(
                    (
                        row["character"],
                        json_text(row["meanings"]),
                        json_text(row["kun_readings"]),
                        json_text(row["on_readings"]),
                        json_text(row["name_readings"]),
                        row["stroke_count"],
                        row["grade"],
                        row["jlpt"],
                        row["unicode"],
                        row["power"],
                        row["source"],
                        row["cached_at"],
                    )
                )
        cur.execute(
            f"""
                insert into kanji_entries(
                    {columns}
                )
                select {columns} from tmp_kanji_entries
                on conflict (character) do update set
                    meanings = excluded.meanings,
                    kun_readings = excluded.kun_readings,
                    on_readings = excluded.on_readings,
                    name_readings = excluded.name_readings,
                    stroke_count = excluded.stroke_count,
                    grade = excluded.grade,
                    jlpt = excluded.jlpt,
                    unicode = excluded.unicode,
                    power = excluded.power,
                    source = excluded.source,
                    cached_at = excluded.cached_at
            """
        )
    print(f"kanji_progress={len(rows)}/{len(rows)}", flush=True)
    target.commit()
    return len(rows)


def sync_questions(source: sqlite3.Connection, target: psycopg.Connection) -> int:
    rows = source.execute(
        "select id, jlpt_level, difficulty, question_type, prompt, content_en, content_ja "
        "from questions"
    ).fetchall()
    columns = "id, jlpt_level, difficulty, question_type, prompt, content_en, content_ja"
    with target.cursor() as cur:
        cur.execute(
            """
            create temporary table tmp_questions(
                id integer,
                jlpt_level varchar(2),
                difficulty varchar(20),
                question_type varchar(40),
                prompt varchar(255),
                content_en json,
                content_ja json
            ) on commit drop
            """
        )
        with cur.copy(f"copy tmp_questions({columns}) from stdin") as copy:
            for row in rows:
                copy.write_row(
                    (
                        row["id"],
                        row["jlpt_level"],
                        row["difficulty"],
                        row["question_type"],
                        row["prompt"],
                        json_text(row["content_en"]),
                        json_text(row["content_ja"]),
                    )
                )
        cur.execute(
            f"""
                insert into questions(
                    {columns}
                )
                select {columns} from tmp_questions
                on conflict (id) do update set
                    jlpt_level = excluded.jlpt_level,
                    difficulty = excluded.difficulty,
                    question_type = excluded.question_type,
                    prompt = excluded.prompt,
                    content_en = excluded.content_en,
                    content_ja = excluded.content_ja
            """
        )
    print(f"question_progress={len(rows)}/{len(rows)}", flush=True)
    target.commit()
    return len(rows)


def sync_weapons(source: sqlite3.Connection, target: psycopg.Connection) -> int:
    rows = source.execute(
        "select id, name, required_role, price, attack_bonus, description from weapons"
    ).fetchall()
    columns = "id, name, required_role, price, attack_bonus, description"
    with target.cursor() as cur:
        cur.execute(
            """
            create temporary table tmp_weapons(
                id varchar(40),
                name varchar(80),
                required_role varchar(40),
                price integer,
                attack_bonus integer,
                description text
            ) on commit drop
            """
        )
        with cur.copy(f"copy tmp_weapons({columns}) from stdin") as copy:
            for row in rows:
                copy.write_row(
                    (
                        row["id"],
                        row["name"],
                        row["required_role"],
                        row["price"],
                        row["attack_bonus"],
                        row["description"],
                    )
                )
        cur.execute(
            f"""
                insert into weapons(id, name, required_role, price, attack_bonus, description)
                select {columns} from tmp_weapons
                on conflict (id) do update set
                    name = excluded.name,
                    required_role = excluded.required_role,
                    price = excluded.price,
                    attack_bonus = excluded.attack_bonus,
                    description = excluded.description
            """
        )
    target.commit()
    return len(rows)


def print_counts(target: psycopg.Connection) -> None:
    with target.cursor() as cur:
        for table in ["kanji_entries", "questions", "weapons", "player_profiles", "scores"]:
            cur.execute(f"select count(*) from {table}")
            print(f"{table}={cur.fetchone()[0]}", flush=True)


def main() -> None:
    source = sqlite3.connect(SQLITE_PATH)
    source.row_factory = sqlite3.Row
    with source, connect_with_retry() as target:
        ensure_online_schema(target)
        print(f"kanji_synced={sync_kanji(source, target)}", flush=True)
        print(f"questions_synced={sync_questions(source, target)}", flush=True)
        print(f"weapons_synced={sync_weapons(source, target)}", flush=True)
        print_counts(target)


if __name__ == "__main__":
    main()
