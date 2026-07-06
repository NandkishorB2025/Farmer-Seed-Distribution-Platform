from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.modules.seed_portal.services import SeedPortalService


seed_portal_bp = Blueprint("seed_portal", __name__)
service = SeedPortalService()


@seed_portal_bp.route("/")
def dashboard():
    return render_template("dashboard.html", **service.dashboard_context())


@seed_portal_bp.route("/farmers", methods=["GET", "POST"])
def farmers():
    if request.method == "POST":
        result = service.register_farmer(request.form)
        flash(result.message, "success" if result.success else "error")
        return redirect(url_for("seed_portal.farmers"))

    return render_template("farmers.html", **service.farmers_context())


@seed_portal_bp.route("/seeds", methods=["GET", "POST"])
def seeds():
    if request.method == "POST":
        result = service.add_seed(request.form)
        flash(result.message, "success" if result.success else "error")
        return redirect(url_for("seed_portal.seeds"))

    return render_template("seeds.html", **service.seeds_context())


@seed_portal_bp.route("/distributions", methods=["GET", "POST"])
def distributions():
    if request.method == "POST":
        result = service.record_distribution(request.form)
        flash(result.message, "success" if result.success else "error")
        return redirect(url_for("seed_portal.distributions"))

    return render_template("distributions.html", **service.distributions_context())


@seed_portal_bp.route("/reports")
def reports():
    return render_template("reports.html", **service.reports_context())
