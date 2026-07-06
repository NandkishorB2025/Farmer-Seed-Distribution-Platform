from __future__ import annotations

from typing import Any

from seed_platform.core.database import execute, query


class SeedPortalRepository:
    def dashboard_stats(self) -> dict[str, float | int]:
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

    def recent_distributions(self, limit: int = 8) -> list[Any]:
        return query(
            """
            SELECT d.id, d.quantity_kg, d.subsidy_percent, d.total_cost, d.distributed_on,
                   f.name AS farmer_name, f.village, s.name AS seed_name
            FROM distributions d
            JOIN farmers f ON f.id = d.farmer_id
            JOIN seeds s ON s.id = d.seed_id
            ORDER BY d.distributed_on DESC, d.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def low_stock_seeds(self) -> list[Any]:
        return query(
            """
            SELECT * FROM seeds
            WHERE stock_kg <= reorder_level_kg
            ORDER BY stock_kg ASC
            """
        )

    def list_farmers(self) -> list[Any]:
        return query("SELECT * FROM farmers ORDER BY registered_on DESC, id DESC")

    def list_farmers_by_name(self) -> list[Any]:
        return query("SELECT * FROM farmers ORDER BY name")

    def create_farmer(
        self,
        name: str,
        village: str,
        phone: str,
        land_acres: float,
        crop_preference: str,
        registered_on: str,
    ) -> None:
        execute(
            """
            INSERT INTO farmers
                (name, village, phone, land_acres, crop_preference, registered_on)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, village, phone, land_acres, crop_preference, registered_on),
        )

    def list_seeds(self) -> list[Any]:
        return query("SELECT * FROM seeds ORDER BY crop_type, name")

    def list_available_seeds(self) -> list[Any]:
        return query("SELECT * FROM seeds WHERE stock_kg > 0 ORDER BY crop_type, name")

    def get_seed(self, seed_id: int) -> Any | None:
        rows = query("SELECT * FROM seeds WHERE id = ?", (seed_id,))
        return rows[0] if rows else None

    def create_seed(
        self,
        name: str,
        crop_type: str,
        variety: str,
        season: str,
        price_per_kg: float,
        stock_kg: float,
        reorder_level_kg: float,
    ) -> None:
        execute(
            """
            INSERT INTO seeds
                (name, crop_type, variety, season, price_per_kg, stock_kg, reorder_level_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, crop_type, variety, season, price_per_kg, stock_kg, reorder_level_kg),
        )

    def create_distribution(
        self,
        farmer_id: int,
        seed_id: int,
        quantity_kg: float,
        subsidy_percent: float,
        total_cost: float,
        distributed_on: str,
        notes: str,
    ) -> None:
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
                total_cost,
                distributed_on,
                notes,
            ),
        )

    def reduce_seed_stock(self, seed_id: int, quantity_kg: float) -> None:
        execute("UPDATE seeds SET stock_kg = stock_kg - ? WHERE id = ?", (quantity_kg, seed_id))

    def list_distributions(self) -> list[Any]:
        return query(
            """
            SELECT d.*, f.name AS farmer_name, f.village, s.name AS seed_name, s.crop_type
            FROM distributions d
            JOIN farmers f ON f.id = d.farmer_id
            JOIN seeds s ON s.id = d.seed_id
            ORDER BY d.distributed_on DESC, d.id DESC
            """
        )

    def report_by_crop(self) -> list[Any]:
        return query(
            """
            SELECT s.crop_type, COALESCE(SUM(d.quantity_kg), 0) AS quantity_kg,
                   COALESCE(SUM(d.total_cost), 0) AS revenue
            FROM seeds s
            LEFT JOIN distributions d ON d.seed_id = s.id
            GROUP BY s.crop_type
            ORDER BY quantity_kg DESC
            """
        )

    def report_by_village(self) -> list[Any]:
        return query(
            """
            SELECT f.village, COUNT(DISTINCT f.id) AS farmers_served,
                   COALESCE(SUM(d.quantity_kg), 0) AS quantity_kg
            FROM farmers f
            LEFT JOIN distributions d ON d.farmer_id = f.id
            GROUP BY f.village
            ORDER BY quantity_kg DESC
            """
        )
