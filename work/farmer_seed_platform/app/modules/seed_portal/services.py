from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.modules.seed_portal.repositories import SeedPortalRepository


@dataclass(frozen=True)
class ServiceResult:
    success: bool
    message: str


class SeedPortalService:
    def __init__(self, repository: SeedPortalRepository | None = None) -> None:
        self.repository = repository or SeedPortalRepository()

    def dashboard_context(self) -> dict:
        return {
            "stats": self.repository.dashboard_stats(),
            "recent_distributions": self.repository.recent_distributions(),
            "low_stock": self.repository.low_stock_seeds(),
        }

    def farmers_context(self) -> dict:
        return {"farmers": self.repository.list_farmers()}

    def register_farmer(self, form_data) -> ServiceResult:
        name = form_data["name"].strip()
        village = form_data["village"].strip()
        phone = form_data["phone"].strip()
        crop_preference = form_data["crop_preference"].strip()
        land_acres = float(form_data["land_acres"])

        self.repository.create_farmer(
            name=name,
            village=village,
            phone=phone,
            land_acres=land_acres,
            crop_preference=crop_preference,
            registered_on=date.today().isoformat(),
        )
        return ServiceResult(True, f"Registered farmer {name}.")

    def seeds_context(self) -> dict:
        return {"seeds": self.repository.list_seeds()}

    def add_seed(self, form_data) -> ServiceResult:
        self.repository.create_seed(
            name=form_data["name"].strip(),
            crop_type=form_data["crop_type"].strip(),
            variety=form_data["variety"].strip(),
            season=form_data["season"].strip(),
            price_per_kg=float(form_data["price_per_kg"]),
            stock_kg=float(form_data["stock_kg"]),
            reorder_level_kg=float(form_data["reorder_level_kg"]),
        )
        return ServiceResult(True, "Seed stock added.")

    def distributions_context(self) -> dict:
        return {
            "distributions": self.repository.list_distributions(),
            "farmers": self.repository.list_farmers_by_name(),
            "seeds": self.repository.list_available_seeds(),
        }

    def record_distribution(self, form_data) -> ServiceResult:
        farmer_id = int(form_data["farmer_id"])
        seed_id = int(form_data["seed_id"])
        quantity_kg = float(form_data["quantity_kg"])
        subsidy_percent = float(form_data["subsidy_percent"])
        notes = form_data.get("notes", "").strip()

        seed = self.repository.get_seed(seed_id)
        if not seed:
            return ServiceResult(False, "Selected seed was not found.")

        if quantity_kg > seed["stock_kg"]:
            return ServiceResult(False, "Distribution quantity exceeds available stock.")

        gross_cost = quantity_kg * seed["price_per_kg"]
        total_cost = round(gross_cost * (1 - subsidy_percent / 100), 2)

        self.repository.create_distribution(
            farmer_id=farmer_id,
            seed_id=seed_id,
            quantity_kg=quantity_kg,
            subsidy_percent=subsidy_percent,
            total_cost=total_cost,
            distributed_on=datetime.now().strftime("%Y-%m-%d %H:%M"),
            notes=notes,
        )
        self.repository.reduce_seed_stock(seed_id, quantity_kg)
        return ServiceResult(True, "Seed distribution recorded and stock updated.")

    def reports_context(self) -> dict:
        return {
            "by_crop": self.repository.report_by_crop(),
            "by_village": self.repository.report_by_village(),
        }
