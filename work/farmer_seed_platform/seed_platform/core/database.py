from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from flask import Flask, current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE_PATH"])
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error: Exception | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def execute(sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur


def query(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return get_db().execute(sql, params).fetchall()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()


def init_db() -> None:
    schema_path = Path(__file__).resolve().parents[1] / "modules" / "seed_portal" / "schema.sql"
    db = get_db()
    db.executescript(schema_path.read_text(encoding="utf-8"))
    seed_initial_data(db)
    db.commit()


def seed_initial_data(db: sqlite3.Connection) -> None:
    farmers_count = db.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
    seeds_count = db.execute("SELECT COUNT(*) FROM seeds").fetchone()[0]

    if farmers_count == 0:
        db.executemany(
            """
            INSERT INTO farmers
                (name, village, phone, land_acres, crop_preference, registered_on)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("Asha Devi", "Rampur", "9876543210", 2.5, "Paddy", date.today().isoformat()),
                ("Ravi Kumar", "Nandgaon", "9876501234", 4.0, "Wheat", date.today().isoformat()),
                ("Meena Singh", "Bhagwanpur", "9876512345", 1.2, "Maize", date.today().isoformat()),
            ],
        )

    if seeds_count == 0:
        db.executemany(
            """
            INSERT INTO seeds
                (name, crop_type, variety, season, price_per_kg, stock_kg, reorder_level_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Paddy Certified Seed", "Paddy", "Swarna", "Kharif", 42.0, 650.0, 120.0),
                ("Wheat Certified Seed", "Wheat", "HD-2967", "Rabi", 36.0, 480.0, 100.0),
                ("Maize Hybrid Seed", "Maize", "HQPM-1", "Kharif", 75.0, 210.0, 60.0),
                ("Mustard Seed", "Mustard", "Pusa Bold", "Rabi", 62.0, 90.0, 40.0),
            ],
        )
