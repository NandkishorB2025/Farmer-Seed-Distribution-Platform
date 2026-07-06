from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.core.database import execute, query


seed_portal_bp = Blueprint("seed_portal", __name__)


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


@seed_portal_bp.route("/")
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


@seed_portal_bp.route("/farmers", methods=["GET", "POST"])
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
        return redirect(url_for("seed_portal.farmers"))

    farmer_rows = query("SELECT * FROM farmers ORDER BY registered_on DESC, id DESC")
    return render_template("farmers.html", farmers=farmer_rows)


@seed_portal_bp.route("/seeds", methods=["GET", "POST"])
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
        return redirect(url_for("seed_portal.seeds"))

    seed_rows = query("SELECT * FROM seeds ORDER BY crop_type, name")
    return render_template("seeds.html", seeds=seed_rows)


@seed_portal_bp.route("/distributions", methods=["GET", "POST"])
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
            return redirect(url_for("seed_portal.distributions"))

        seed_row = seed[0]
        if quantity_kg > seed_row["stock_kg"]:
            flash("Distribution quantity exceeds available stock.", "error")
            return redirect(url_for("seed_portal.distributions"))

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
        return redirect(url_for("seed_portal.distributions"))

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


@seed_portal_bp.route("/reports")
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
