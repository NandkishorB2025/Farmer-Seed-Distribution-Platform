from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "seed_platform.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-change-me"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return get_db().execute(sql, params).fetchall()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            village TEXT NOT NULL,
            phone TEXT NOT NULL,
            land_acres REAL NOT NULL CHECK (land_acres > 0),
            crop_preference TEXT NOT NULL,
            registered_on TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS seeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            variety TEXT NOT NULL,
            season TEXT NOT NULL,
            price_per_kg REAL NOT NULL CHECK (price_per_kg >= 0),
            stock_kg REAL NOT NULL CHECK (stock_kg >= 0),
            reorder_level_kg REAL NOT NULL CHECK (reorder_level_kg >= 0)
        );

        CREATE TABLE IF NOT EXISTS distributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            seed_id INTEGER NOT NULL,
            quantity_kg REAL NOT NULL CHECK (quantity_kg > 0),
            subsidy_percent REAL NOT NULL CHECK (subsidy_percent >= 0 AND subsidy_percent <= 100),
            total_cost REAL NOT NULL CHECK (total_cost >= 0),
            distributed_on TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id),
            FOREIGN KEY (seed_id) REFERENCES seeds(id)
        );
        """
    )

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

    db.commit()
    db.close()


def dashboard_stats() -> dict[str, float | int]:
    rows = query(
        """
        SELECT
            (SELECT COUNT(*) FROM farmers) AS farmer_count,
            (SELECT COUNT(*) FROM seeds) AS seed_count,
            (SELECT COALESCE(SUM(stock_kg), 0) FROM seeds) AS stock_kg,
            (SELECT COALESCE(SUM(quantity_kg), 0) FROM distributions) AS distributed_kg,
            (SELECT COUNT(*) FROM seeds WHERE stock_kg <= reorder_level_kg) AS low_stock_count
        """
    )
    return dict(rows[0])


@app.route("/")
def dashboard():
    recent_distributions = query(
        """
        SELECT d.id, d.quantity_kg, d.subsidy_percent, d.total_cost, d.distributed_on,
               f.name AS farmer_name, f.village, s.name AS seed_name
        FROM distributions d
        JOIN farmers f ON f.id = d.farmer_id
        JOIN seeds s ON s.id = d.seed_id
        ORDER BY d.distributed_on DESC, d.id DESC
        LIMIT 8
        """
    )
    low_stock = query(
        """
        SELECT * FROM seeds
        WHERE stock_kg <= reorder_level_kg
        ORDER BY stock_kg ASC
        """
    )
    return render_template(
        "dashboard.html",
        stats=dashboard_stats(),
        recent_distributions=recent_distributions,
        low_stock=low_stock,
    )


@app.route("/farmers", methods=["GET", "POST"])
def farmers():
    if request.method == "POST":
        name = request.form["name"].strip()
        village = request.form["village"].strip()
        phone = request.form["phone"].strip()
        crop_preference = request.form["crop_preference"].strip()
        land_acres = float(request.form["land_acres"])

        execute(
            """
            INSERT INTO farmers
                (name, village, phone, land_acres, crop_preference, registered_on)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, village, phone, land_acres, crop_preference, date.today().isoformat()),
        )
        flash(f"Registered farmer {name}.", "success")
        return redirect(url_for("farmers"))

    farmer_rows = query("SELECT * FROM farmers ORDER BY registered_on DESC, id DESC")
    return render_template("farmers.html", farmers=farmer_rows)


@app.route("/seeds", methods=["GET", "POST"])
def seeds():
    if request.method == "POST":
        execute(
            """
            INSERT INTO seeds
                (name, crop_type, variety, season, price_per_kg, stock_kg, reorder_level_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.form["name"].strip(),
                request.form["crop_type"].strip(),
                request.form["variety"].strip(),
                request.form["season"].strip(),
                float(request.form["price_per_kg"]),
                float(request.form["stock_kg"]),
                float(request.form["reorder_level_kg"]),
            ),
        )
        flash("Seed stock added.", "success")
        return redirect(url_for("seeds"))

    seed_rows = query("SELECT * FROM seeds ORDER BY crop_type, name")
    return render_template("seeds.html", seeds=seed_rows)


@app.route("/distributions", methods=["GET", "POST"])
def distributions():
    if request.method == "POST":
        farmer_id = int(request.form["farmer_id"])
        seed_id = int(request.form["seed_id"])
        quantity_kg = float(request.form["quantity_kg"])
        subsidy_percent = float(request.form["subsidy_percent"])
        notes = request.form.get("notes", "").strip()

        seed = query("SELECT * FROM seeds WHERE id = ?", (seed_id,))
        if not seed:
            flash("Selected seed was not found.", "error")
            return redirect(url_for("distributions"))

        seed_row = seed[0]
        if quantity_kg > seed_row["stock_kg"]:
            flash("Distribution quantity exceeds available stock.", "error")
            return redirect(url_for("distributions"))

        gross_cost = quantity_kg * seed_row["price_per_kg"]
        total_cost = gross_cost * (1 - subsidy_percent / 100)

        execute(
            """
            INSERT INTO distributions
                (farmer_id, seed_id, quantity_kg, subsidy_percent, total_cost, distributed_on, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                farmer_id,
                seed_id,
                quantity_kg,
                subsidy_percent,
                round(total_cost, 2),
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                notes,
            ),
        )
        execute("UPDATE seeds SET stock_kg = stock_kg - ? WHERE id = ?", (quantity_kg, seed_id))
        flash("Seed distribution recorded and stock updated.", "success")
        return redirect(url_for("distributions"))

    distribution_rows = query(
        """
        SELECT d.*, f.name AS farmer_name, f.village, s.name AS seed_name, s.crop_type
        FROM distributions d
        JOIN farmers f ON f.id = d.farmer_id
        JOIN seeds s ON s.id = d.seed_id
        ORDER BY d.distributed_on DESC, d.id DESC
        """
    )
    return render_template(
        "distributions.html",
        distributions=distribution_rows,
        farmers=query("SELECT * FROM farmers ORDER BY name"),
        seeds=query("SELECT * FROM seeds WHERE stock_kg > 0 ORDER BY crop_type, name"),
    )


@app.route("/reports")
def reports():
    by_crop = query(
        """
        SELECT s.crop_type, COALESCE(SUM(d.quantity_kg), 0) AS quantity_kg,
               COALESCE(SUM(d.total_cost), 0) AS revenue
        FROM seeds s
        LEFT JOIN distributions d ON d.seed_id = s.id
        GROUP BY s.crop_type
        ORDER BY quantity_kg DESC
        """
    )
    by_village = query(
        """
        SELECT f.village, COUNT(DISTINCT f.id) AS farmers_served,
               COALESCE(SUM(d.quantity_kg), 0) AS quantity_kg
        FROM farmers f
        LEFT JOIN distributions d ON d.farmer_id = f.id
        GROUP BY f.village
        ORDER BY quantity_kg DESC
        """
    )
    return render_template("reports.html", by_crop=by_crop, by_village=by_village)


init_db()


if __name__ == "__main__":
    app.run(debug=True)
